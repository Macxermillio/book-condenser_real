RANGE_USER_PROMPT = """
You will be provided with a list of text chunks from a book, each with a chunk_id and chunk of text. The chunk_id is an integer that corresponds to the order of the chunks in the original text.

Your task is to identify the ranges of actual book chapters in the text. IMPORTANT: Only identify ranges that contain the main narrative chapters of the book. Do NOT include:
- Front matter (title pages, copyright, table of contents, prefaces, acknowledgments, etc.)
- Back matter (appendices, glossaries, indexes, author bios, etc.)

For each chapter you identify, provide:
- start: chunk_id where the chapter begins (this should always include the chapter title and number if they are present in the text)
- end: chunk_id where the chapter ends
- chapter_number: the chapter number as an integer (if present, e.g., 1 for "Chapter 1")
- chapter_title: the chapter title as a string (if present, e.g., "The Beginning")

If a chapter has no number, set chapter_number to null. If a chapter has no title, set chapter_title to null.

Here is the list of text chunks:
{chunks}

Return the chapter ranges with their numbers and titles where available.
"""

"""You will be provided with a list of text chunks from a book, each with a chunk_id and chunk of text. The chunk_id is an integer that corresponds to the order of the chunks in the original text.

Your task is to identify the ranges of actual book chapters in the text. IMPORTANT: Only identify ranges that contain the main narrative chapters of the book. Do NOT include:
- Front matter (title pages, copyright, table of contents, prefaces, acknowledgments, etc.)
- Back matter (appendices, glossaries, indexes, author bios, etc.)

For each chapter you identify, provide:
- start: chunk_id where the chapter begins (this should always include the chapter title and number if they are present in the text)
- end: chunk_id where the chapter ends
- chapter_number: the chapter number as an integer (if present, e.g., 1 for "Chapter 1")
- chapter_title: the chapter title as a string (if present, e.g., "The Beginning")

If a chapter has no number, set chapter_number to null. If a chapter has no title, set chapter_title to null.

Here is the list of text chunks:
{chunks}

Return the chapter ranges with their numbers and titles where available. Return them in JSON format as a list of objects with the keys: start, end, chapter_number, chapter_title.
"""