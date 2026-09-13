# Benchmark status

The benchmark harness has been executed in the current sandbox. The fixed 15-case manifest was generated successfully, but no neural WAV files were produced because this sandbox cannot install/download the Kokoro or Transformers model packages/weights.

This is an environment limitation, not a fallback to eSpeak. Robotic eSpeak output remains disabled.

Use `experiments/neural_voice_benchmark_colab.ipynb` in an internet-enabled Colab to run the exact same benchmark and render the neural WAV comparison.
