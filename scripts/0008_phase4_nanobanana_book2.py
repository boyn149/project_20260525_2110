import os
import asyncio
from pathlib import Path
from google import genai
from google.genai import types

# Config
GITHUB_OWNER = "boyn149"
GITHUB_REPO = "project_20260525_2110"
MODEL_ID = "gemini-3.1-flash-image-preview"

async def generate_images_nanobanana():
    print(f"--- Continuing Phase 4 for Book 2 using Nanobanana ({MODEL_ID}) ---")
    
    # Initialize Gemini client
    client = genai.Client()

    pic_details_path = Path("pic_ture_details.md")
    pic_content = pic_details_path.read_text(encoding="utf-8")

    # Extract book2 prompts
    book2_prompts = []
    found_book2 = False
    for line in pic_content.splitlines():
        if "Book Code: book2" in line:
            found_book2 = True
        elif found_book2 and line.startswith("- [PROMPT:"):
            p = line[2:].strip()
            book2_prompts.append(p)
        elif found_book2 and line.startswith("## Book Code:"):
            break

    pic_dir_2 = Path("book/book_book2/pic_book2")
    pic_dir_2.mkdir(parents=True, exist_ok=True)
    
    book2_files = list(Path("book/book_book2").glob("book_book2_*.md"))
    if not book2_files:
        print("Error: Book 2 file not found.")
        return
    book2_file = book2_files[0]

    # Starting from image 9 (index 8)
    start_index = 8
    for i in range(start_index, len(book2_prompts)):
        n = i + 1
        prompt = book2_prompts[i]
        filename = f"infographic_book2_{n}.png"
        filepath = pic_dir_2 / filename

        print(f"\n[{n}/{len(book2_prompts)}] Generating: {filename}")
        print(f"Prompt: {prompt[:100]}...")
        
        try:
            # 1. Generate Image
            prompt_text = prompt[8:-1]
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=[prompt_text],
            )

            # 2. Save Image
            success = False
            for part in response.parts:
                if part.inline_data is not None:
                    image = part.as_image()
                    image.save(str(filepath))
                    print(f"Saved: {filepath}")
                    success = True
                    break
            
            if success:
                # 3. Embed URL in Markdown
                book2_content = book2_file.read_text(encoding="utf-8")
                raw_url = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/main/book/book_book2/pic_book2/{filename}"
                embed_url = f"![{prompt_text}]({raw_url})"
                
                if prompt in book2_content:
                    book2_content = book2_content.replace(prompt, embed_url, 1)
                    book2_file.write_text(book2_content, encoding="utf-8")
                    print(f"Successfully embedded URL in {book2_file.name}")
                    
                    # 4. Git Upload (Commit both image and book file)
                    os.system(f'git add "{filepath}" "{book2_file}"')
                    os.system(f'git commit -m "Add {filename} and update book (via Nanobanana)"')
                    os.system('git pull origin main --rebase')
                    os.system('git push origin main')
                else:
                    print(f"Warning: Prompt not found in {book2_file.name}")
                    # Still commit the image
                    os.system(f'git add "{filepath}"')
                    os.system(f'git commit -m "Add {filename} (via Nanobanana)"')
                    os.system('git pull origin main --rebase')
                    os.system('git push origin main')

            else:
                print(f"Failed to generate {filename}: No image data.")

        except Exception as e:
            print(f"Error during processing {filename}: {e}")
            if "429" in str(e) or "QUOTA_EXHAUSTED" in str(e).upper():
                break

        print("Waiting 10 seconds before next request...")
        await asyncio.sleep(10)

    print("\n--- Nanobanana Script Finished ---")

if __name__ == "__main__":
    asyncio.run(generate_images_nanobanana())
