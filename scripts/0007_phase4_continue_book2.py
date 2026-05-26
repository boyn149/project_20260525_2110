import asyncio
import os
from pathlib import Path
import sys

# Add notebooklm-py-light to sys.path if needed
sys.path.append(str(Path("notebooklm-py-light").absolute()))

try:
    from notebooklm import NotebookLMClient, InfographicOrientation
except ImportError:
    # If it's not in the folder directly, try normal import
    from notebooklm import NotebookLMClient, InfographicOrientation

# Config
NOTEBOOK_ID = "e0d58c1c-dc32-4acc-ab94-41cb782a0bea"
GITHUB_OWNER = "boyn149"
GITHUB_REPO = "project_20260525_2110"

async def continue_book2():
    print("--- Continuing Phase 4 for Book 2 using NotebookLM ---")
    async with await NotebookLMClient.from_storage() as client:
        pic_details_path = Path("pic_ture_details.md")
        pic_content = pic_details_path.read_text(encoding="utf-8")

        # Extract book2 prompts
        book2_prompts = []
        found_book2 = False
        for line in pic_content.splitlines():
            if "Book Code: book2" in line:
                found_book2 = True
            elif found_book2 and line.startswith("- [PROMPT:"):
                # Clean up the prompt to match exact string in file
                p = line[2:].strip()
                book2_prompts.append(p)
            elif found_book2 and line.startswith("## Book Code:"):
                break # Next book or section

        pic_dir_2 = Path("book/book_book2/pic_book2")
        pic_dir_2.mkdir(parents=True, exist_ok=True)
        
        book2_files = list(Path("book/book_book2").glob("book_book2_*.md"))
        if not book2_files:
            print("Error: Book 2 file not found.")
            return
        book2_file = book2_files[0]
        book2_content = book2_file.read_text(encoding="utf-8")

        # Starting from image 5 (index 4)
        start_index = 4
        for i in range(start_index, len(book2_prompts)):
            n = i + 1
            prompt = book2_prompts[i]
            filename = f"infographic_book2_{n}.png"
            filepath = pic_dir_2 / filename

            print(f"\n[{n}/{len(book2_prompts)}] Generating: {filename}")
            print(f"Prompt: {prompt[:100]}...")
            
            try:
                # 1. Generate Infographic
                status = await client.artifacts.generate_infographic(
                    NOTEBOOK_ID,
                    instructions=prompt,
                    orientation=InfographicOrientation.LANDSCAPE
                )
                print(f"Task ID: {status.task_id}. Waiting for completion...")
                
                # 2. Wait for completion
                final_status = await client.artifacts.wait_for_completion(
                    NOTEBOOK_ID, 
                    status.task_id, 
                    poll_interval=25
                )

                if final_status.is_complete:
                    # 3. Download
                    await client.artifacts.download_infographic(NOTEBOOK_ID, str(filepath))
                    print(f"Downloaded: {filepath}")

                    # 4. Git Upload
                    os.system(f'git add "{filepath}"')
                    os.system(f'git commit -m "Add {filename}"')
                    os.system('git pull origin main --rebase')
                    os.system('git push origin main')

                    # 5. Embed URL in Markdown
                    raw_url = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/main/book/book_book2/pic_book2/{filename}"
                    # Extract prompt text (removing [PROMPT: and ])
                    prompt_text = prompt[8:-1]
                    embed_url = f"![{prompt_text}]({raw_url})"
                    
                    if prompt in book2_content:
                        book2_content = book2_content.replace(prompt, embed_url, 1)
                        book2_file.write_text(book2_content, encoding="utf-8")
                        print(f"Successfully embedded URL in {book2_file.name}")
                    else:
                        print(f"Warning: Prompt not found in {book2_file.name}. It might be already replaced or mismatch.")

                else:
                    print(f"Failed to generate {filename}: {final_status.status}")
                    break # Stop if we hit a limit again
            except Exception as e:
                print(f"Error during processing {filename}: {e}")
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e).upper():
                    print("Rate limit detected. Stopping.")
                    break
                # For other errors, we might want to continue or stop. 
                # Given the history, we'll try to continue once but break if it persists.
                # For now, let's break to be safe.
                break

            print("Waiting 15 seconds before next request...")
            await asyncio.sleep(15)

        # Final commit and push for book file
        os.system(f'git add "{book2_file}"')
        os.system('git commit -m "Update Book 2 with newly generated image URLs"')
        os.system('git pull origin main --rebase')
        os.system('git push origin main')
        print("\n--- Script Finished ---")

if __name__ == "__main__":
    asyncio.run(continue_book2())
