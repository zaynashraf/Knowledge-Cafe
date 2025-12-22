import asyncio
import edge_tts

async def generate_tts(summary_text, output_path, voice="en-US-JennyNeural"):
    communicate = edge_tts.Communicate(summary_text, voice=voice)
    await communicate.save(output_path)

def speak(summary_text, output_path):
    asyncio.run(generate_tts(summary_text, output_path))