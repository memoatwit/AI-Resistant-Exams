from exam_attack import create_exam_variant

# A simple test to check if the attacks work on ex1.tex
watermark_attack = {
    'name': 'A1_watermark_tiled_math',
    'type': 'watermark_tiled',
    'params': {'text': r"f'(x)", 'color': 'gray!15', 'size': 8, 'angle': 20, 'x_step': 4, 'y_step': 3}
}

print("Testing attack on ex1.tex...")
result = create_exam_variant(
    template_path='ex1.tex',
    output_name='test_variant_ex1',
    attack_params=watermark_attack
)

print(f"Result: {result}")
