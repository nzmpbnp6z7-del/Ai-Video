#!/usr/bin/env bash
# Lädt die deutschen Piper-Stimmen (neuronale Offline-TTS) nach ./voices
set -e
cd "$(dirname "$0")"
mkdir -p voices
for v in thorsten karlsson pavoque kerstin ramona eva_k-x; do
  [ -f voices/de-$v-low.onnx ] && continue
  curl -sSL https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-de-$v-low.tar.gz | tar xz -C voices
done
