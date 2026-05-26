RANGE_SYSTEM_PROMPT = """You are an expert at identifying chapter ranges in a list of text chunks from books. Your task is to identify actual book chapters (not front matter like title pages, copyright notices, tables of contents, prefaces, or acknowledgments, and not back matter like appendices, glossaries, indexes, or author bios).

For each chapter you identify:
- Find the start chunk_id where the chapter begins(tthis should always include the chapter title and number if they are present in the text)
- Find the end chunk_id where the chapter ends
- Extract the chapter number (if present, e.g., "Chapter 1", "Chapter 2") as an integer
- Extract the chapter title (if present, e.g., "The Beginning", "A New Hope")

Only identify ranges that contain actual book content chapters. Ignore any front matter (beginning of book) and back matter (end of book) that are not part of the main narrative chapters.
"""

CHAPTER_RANGES_SCHEMA = """{
  "chapter_ranges": [
    {
      "start": <integer>,
      "end": <integer>,
      "chapter_number": <integer or null>,
      "chapter_title": <string or null>
    }
  ]
}"""

RANGE_JSON_INSTRUCTION = (
    "\n\nCRITICAL: Respond with ONLY a valid JSON object — no explanation, "
    "no markdown, no code fences, no text before or after. "
    f"The JSON must match this exact structure:\n{CHAPTER_RANGES_SCHEMA}"
)
