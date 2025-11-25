import asyncio
from playwright.async_api import async_playwright
import httpx
import base64
import json
import logging
from typing import Dict, Any, Optional
import anthropic
import os
from data_processor import DataProcessor

logger = logging.getLogger(__name__)

class QuizSolver:
    def __init__(self, email: str, secret: str):
        self.email = email
        self.secret = secret
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.data_processor = DataProcessor()
        self.http_client = httpx.AsyncClient(timeout=120.0)
        
    async def solve_quiz_chain(self, start_url: str) -> Dict[str, Any]:
        """Solve a chain of quizzes starting from start_url"""
        current_url = start_url
        results = []
        max_iterations = 20  # Prevent infinite loops
        iteration = 0
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            while current_url and iteration < max_iterations:
                iteration += 1
                logger.info(f"Solving quiz {iteration}: {current_url}")
                
                try:
                    # Extract question from the quiz page
                    question_data = await self.extract_question(browser, current_url)
                    logger.info(f"Question extracted: {question_data['question'][:200]}...")
                    
                    # Solve the question using Claude
                    answer = await self.solve_question(question_data)
                    logger.info(f"Answer generated: {answer}")
                    
                    # Submit the answer
                    submit_url = question_data.get('submit_url')
                    if not submit_url:
                        logger.error("No submit URL found in question")
                        break
                    
                    response = await self.submit_answer(
                        submit_url=submit_url,
                        quiz_url=current_url,
                        answer=answer
                    )
                    
                    results.append({
                        "url": current_url,
                        "question": question_data['question'][:200],
                        "answer": answer,
                        "correct": response.get("correct", False),
                        "reason": response.get("reason")
                    })
                    
                    # Check if there's a next URL
                    if response.get("correct") and response.get("url"):
                        current_url = response["url"]
                    elif not response.get("correct") and response.get("url"):
                        # Can retry current or skip to next
                        current_url = response["url"]
                    else:
                        logger.info("Quiz chain completed")
                        break
                        
                except Exception as e:
                    logger.error(f"Error solving quiz at {current_url}: {str(e)}", exc_info=True)
                    results.append({
                        "url": current_url,
                        "error": str(e)
                    })
                    break
            
            await browser.close()
        
        await self.http_client.aclose()
        return {"total_solved": len(results), "results": results}
    
    async def extract_question(self, browser, url: str) -> Dict[str, Any]:
        """Extract question from the quiz page using Playwright"""
        page = await browser.new_page()
        
        try:
            # Navigate to the URL
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for content to load (the #result div or body content)
            await page.wait_for_timeout(2000)
            
            # Get the full HTML content
            html_content = await page.content()
            
            # Get text content
            text_content = await page.evaluate("() => document.body.innerText")
            
            # Try to find links in the page for file downloads
            links = await page.evaluate("""
                () => Array.from(document.querySelectorAll('a')).map(a => ({
                    href: a.href,
                    text: a.innerText
                }))
            """)
            
            return {
                "question": text_content,
                "html": html_content,
                "links": links,
                "submit_url": self.extract_submit_url(text_content)
            }
            
        finally:
            await page.close()
    
    def extract_submit_url(self, text: str) -> Optional[str]:
        """Extract submit URL from question text"""
        import re
        # Look for "Post your answer to https://..."
        match = re.search(r'Post your answer to (https?://[^\s\)]+)', text)
        if match:
            return match.group(1)
        return None
    
    async def solve_question(self, question_data: Dict[str, Any]) -> Any:
        """Use Claude to solve the question"""
        question_text = question_data['question']
        links = question_data.get('links', [])
        
        # Build context for Claude
        context = f"""You are solving a data analysis quiz. Here's the question:

{question_text}

"""
        
        if links:
            context += "\nAvailable links/files:\n"
            for link in links:
                context += f"- {link['text']}: {link['href']}\n"
        
        context += """
Analyze this question and provide ONLY the final answer in the appropriate format:
- For numbers: return just the number (e.g., 12345)
- For text: return just the text without quotes
- For boolean: return true or false
- For JSON objects: return valid JSON
- For images/files: return base64 data URI

Think step by step but end with "FINAL_ANSWER:" followed by just the answer.
"""
        
        # Check if we need to download and process files
        file_contents = {}
        for link in links:
            if any(ext in link['href'].lower() for ext in ['.pdf', '.csv', '.xlsx', '.json', '.txt']):
                try:
                    content = await self.download_file(link['href'])
                    file_contents[link['href']] = content
                except Exception as e:
                    logger.warning(f"Failed to download {link['href']}: {e}")
        
        # If we have files, process them
        if file_contents:
            processed_data = await self.data_processor.process_files(file_contents)
            context += f"\n\nProcessed file data:\n{json.dumps(processed_data, indent=2)[:5000]}"
        
        # Call Claude API
        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": context}
            ]
        )
        
        response_text = message.content[0].text
        
        # Extract the final answer
        answer = self.extract_final_answer(response_text)
        return answer
    
    def extract_final_answer(self, response: str) -> Any:
        """Extract the final answer from Claude's response"""
        import re
        
        # Look for FINAL_ANSWER: marker
        match = re.search(r'FINAL_ANSWER:\s*(.+?)(?:\n|$)', response, re.IGNORECASE | re.DOTALL)
        if match:
            answer = match.group(1).strip()
        else:
            # Take the last line as answer
            lines = [l.strip() for l in response.strip().split('\n') if l.strip()]
            answer = lines[-1] if lines else response.strip()
        
        # Try to parse as JSON
        try:
            return json.loads(answer)
        except:
            pass
        
        # Try to parse as number
        try:
            if '.' in answer:
                return float(answer)
            return int(answer)
        except:
            pass
        
        # Try to parse as boolean
        if answer.lower() in ['true', 'false']:
            return answer.lower() == 'true'
        
        # Return as string
        return answer
    
    async def download_file(self, url: str) -> bytes:
        """Download a file from URL"""
        response = await self.http_client.get(url)
        response.raise_for_status()
        return response.content
    
    async def submit_answer(self, submit_url: str, quiz_url: str, answer: Any) -> Dict[str, Any]:
        """Submit answer to the quiz endpoint"""
        payload = {
            "email": self.email,
            "secret": self.secret,
            "url": quiz_url,
            "answer": answer
        }
        
        logger.info(f"Submitting to {submit_url}: {payload}")
        
        response = await self.http_client.post(
            submit_url,
            json=payload,
            timeout=30.0
        )
        
        response.raise_for_status()
        result = response.json()
        logger.info(f"Submit response: {result}")
        
        return result