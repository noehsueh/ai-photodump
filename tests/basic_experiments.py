# %%
import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForVision2Seq
from transformers.image_utils import load_image

DEVICE = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"

# Load three images
image_1 = load_image("/Users/noehsueh/Projects/Personal/photo-dump-ai/album/9D72E917-AACD-4E50-9D79-E9B6A7CA9958.jpg")
image_2 = load_image("/Users/noehsueh/Projects/Personal/photo-dump-ai/album/IMG_20230110_110110232_HDR.jpg")
image_3 = load_image("/Users/noehsueh/Projects/Personal/photo-dump-ai/album/AA003.jpg")
# load photodump_list.txt
with open("/Users/noehsueh/Projects/Personal/photo-dump-ai/photodump_list.txt", "r") as f:
    photodump_list = f.read()

# Initialize processor and model
processor = AutoProcessor.from_pretrained("HuggingFaceTB/SmolVLM-256M-Instruct")
model = AutoModelForVision2Seq.from_pretrained(
    "HuggingFaceTB/SmolVLM-256M-Instruct",
    torch_dtype=torch.bfloat16,
    _attn_implementation="flash_attention_2" if DEVICE == "cuda" else "eager",
).to(DEVICE)
# %%
# Create input messages
messages = [
    {
        "role": "user",
        "content": [
            {"type": "image"},
            {"type": "image"},
            # {"type": "image"},
            # {"type": "text", "text": "Can you describe this two images?"}
            {"type": "text", 
             "text": "You are an expert image classifier. Given a list of input image, classify it into one of the following categories based on its main subject and style:" + photodump_list + 
             "\n Return the results in the following format: category_name: [image_number(s)]"
             }
        ]
    },
]
# %%
# Prepare inputs
prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
inputs = processor(text=prompt, images=[image_1, image_2], return_tensors="pt")
inputs = inputs.to(DEVICE)

# Generate outputs
generated_ids = model.generate(**inputs, max_new_tokens=1000)
generated_texts = processor.batch_decode(
    generated_ids,
    skip_special_tokens=True,
)

print(generated_texts[0])
# %%
import torch
from transformers import Qwen2_5_VLForConditionalGeneration, AutoTokenizer, AutoProcessor
from qwen_vl_utils import process_vision_info

model = model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-VL-7B-Instruct",
    torch_dtype=torch.bfloat16,
    # attn_implementation="flash_attention_2",
    device_map="auto",
)

processor = AutoProcessor.from_pretrained("Qwen/Qwen2.5-VL-7B-Instruct")
#%%
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "image",
                "image": "/Users/noehsueh/Projects/Personal/photo-dump-ai/album/9D72E917-AACD-4E50-9D79-E9B6A7CA9958.jpg",
            },
            {"type": "text", "text": "Describe this image."},
        ],
    }
]

# Preparation for inference
text = processor.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True
)
image_inputs, video_inputs = process_vision_info(messages)
inputs = processor(
    text=[text],
    images=image_inputs,
    videos=video_inputs,
    padding=True,
    return_tensors="pt",
)
inputs = inputs.to("cuda")

# Inference: Generation of the output
generated_ids = model.generate(**inputs, max_new_tokens=128)
generated_ids_trimmed = [
    out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
]
output_text = processor.batch_decode(
    generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
)
print(output_text)