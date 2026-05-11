# Karpathy — Intro to LLMs (notes)

## Q&A

1. In one sentence, what is the training objective of a base LLM? Training objective of LLM is to encode the knowledge of the training data in model's parameters

3. What's the difference between pre-training and post-training (fine-tuning)? Pre-training give the model it's knowledge via parameter weights. Post-training or fine-tuning is to align the model to generate the response in a desired format with the required guardrails.

4. Why does an LLM "hallucinate"? What's the mechanical cause, not the symptom? Given a set of words, via promots, the LLM Is trying to generate the response by fining the next best words. The model doesn't necessarily stored the exact information via its parameters. It tries to generate a response in an expected structure. So it fills in the data, sometimes incorrectly *thus hallucinating", just to keep the output as per it's learned formats. 

5. What is a "context window" — and what physically happens at the model when you exceed it? The context window is the maximum length of the input text that can be given to the model. When the length is exceeded, the model automatically truncated the earlier part of the stored data, making the output less accurate. 

6. Why is RLHF needed at all if pre-training already produces a coherent model? Reinforced Learning via Human Feedback helps with further fine-tuning of the model by training it for the desirable output format from a paried list of output evaluated by a human. 

7. Tool use / function calling — what is the LLM actually outputting when it "calls a tool"? It outputs the parameters requred to call the tool for the required information. 

8. What does Karpathy mean by "LLM OS"? Give your own analogy. LLMs are no longer just a word prediction tools, the can call multiple external tools, web search, calculation, file access, they can be customized. There are open and closed models, and a host of other customized applications. It's an entire ecosystem of tools and features just like desktop OS.

9. Name 3 jailbreak categories he mentions: Prompt Injection, Data Poisoning, Text-Encoding, Role-playing

10. What's the scaling law claim in one sentence, and what's the practical PM takeaway? Increasing the model parameter and training data increases the accuracy of next word prediction. A model with more parameters, and trained on learge data-set is more accurate or useful for the complex task.  

11. List 2 things in this lecture that surprised you or contradicted a prior assumption: The jailbreak methods (i didn't know about them or thought it was possible), and it would have been the scaling law, but I heard about it in another video. 
