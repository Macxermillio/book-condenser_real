
CONDENSING_PROMPT="""
You are an expert at removing fluff from text ensuring that the writing that is left is almost always useful.
Your job is not to summarize text but take out pieces of text that are not useful, waste time or don't add much to the content.

You have to output the altered text with all the fluff removed. While the text remains pleasurable to read and coherent. If you remove details, make sure the remaining content still remains coherent and makes sense. Also, ensure that the remaining content is still pleasurable to read and coherent.

Examples of useless fluff include:
- hedging words like "very", "really", "just", "actually", "basically", "literally"
- filler phrases like "in my opinion", "I think", "it seems that", "as you know", "at the end of the day"
- redundant phrases like "each and every", "first and foremost", "in conclusion", "in summary", "in order to"
- unnecessary adjectives and adverbs that don't add meaning
- anecdotes or tangential asides that don't contribute to the main points and are never referenced again later in the text.
- overly verbose explanations that could be stated more concisely without losing meaning.
- anecdotes that are too long and can be shortened(ENSURE YOU SHORTEN THEM TO A REASONABLE LENGTH).

When you remove these things ensure the authors voice and style is preserved as much as possible. The text should still feel like it was written by the same person, just with all the fluff removed. Remember to shorten anecdotes that are too long but ensure you shorten them to a reasonable length. You can also remove anecdotes entirely if they are completely irrelevant to the main points of the text or add little to the main points of the text.

Here is the chunk of text to remove fluff from:

{chunk}

You must output all the sections in the text. Every part of it should be in the output but properly altered.
Improtantly, you must use markdown formatting in your output. Use markdown heading 2 for chapter titles and numbers if they exist..
"""