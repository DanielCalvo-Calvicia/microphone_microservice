# 02 — Purpose

> Depends on: 01

| Field | Answer |
|---|---|
| Problem | The robot must hear. Something has to read the local sound input, decide where a spoken phrase starts and ends, and hand each phrase to the rest of the pipeline in the wire format all the services share. |
| Objective | Turn the live microphone into a stream of finished **utterances** (what is said between two silences), as mono PCM16 inside `contracts.stream` events, on request from Brain. |
| Main responsibilities | Open and release the input device; negotiate a format the hardware accepts; downmix to mono; cut the capture into utterances with silence detection and its treatments (DC offset, smoothing, noise floor); optionally resample what is sent; answer `/start`, `/stream`, `/stop`, `/available`, `/health`. |
| Explicit non-responsibilities | No speech to text (STT), no decisions (ai-agent), no playback (speaker), no call to any other service (Brain is the only coordinator), no recording to disk, no authentication (not designed project-wide). |
| Business process | The voice flow: microphone, Brain, STT, Brain (accumulates what was said), ai-agent, Brain, TTS, speaker (`../deployment/docs/DEPLOYMENT.md`). The microphone is its first step. |
| Project boundaries | Owns: the capture and the cutting into utterances. Does not own: the wire format (`contracts`), the logging (`shared-logging`), the deployment (`deployment`), the transcription. |
| Users / consumers | Only Brain. |
| Review policy | The maintainer tests on a real microphone before the service counts as working; unit tests and the end-to-end suite of `contracts` use fake hardware. |
