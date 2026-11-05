# 07 — Data and persistence

> Depends on: 05, 06

| Field | Answer |
|---|---|
| Database | None |
| Schema / migrations tool | NOT APPLICABLE |
| Cache | None |
| State held | In memory only: the `Microphone` state (idle or capturing, with the negotiated format), the open stream, the segmenter of the active capture (volume smoothing, noise floor, the utterance being built). All of it is lost on restart; Brain must call `/start` again |
| Personal data (GDPR) | The audio is a recording of the room and can contain speech, so it is personal data while it exists. It is held in memory until the utterance is sent on the stream, never written to disk and never logged |
| Retention rules | None: an utterance is not kept after it is sent. The utterance in progress is dropped if the device fails; it is sent when the capture is closed |
| Backup policy | NOT APPLICABLE |
| Audit trail | None |
| Files on disk | None written. The git-ignored `.env`, `.env.staging` and `.env.production` hold configuration only; they were not opened |
