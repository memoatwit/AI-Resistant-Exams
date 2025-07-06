import ollama

res = ollama.chat(
	model="gemma3:4b",
	messages=[
		{
			'role': 'user',
			'content': 'Describe this image:',
			'images': ['./ex0.png']
		}
	]
)

print(res['message']['content'])