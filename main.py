from transfer import StyleTransfer

transfer = StyleTransfer(".md/style_input.jpg")

result = transfer.apply_style(".md/cat_input.jpg",1)
result.save("result.jpg")