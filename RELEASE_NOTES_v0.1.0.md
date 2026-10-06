# Rehber Göz Prototype v0.1.0

## Included

- Gemini image analysis test
- Environment-variable based API key
- Basic project versioning
- GitHub Release-ready structure

## Security

The Gemini API key is intentionally NOT included in this release.

The device/user must provide `GEMINI_API_KEY` locally through `.env` or another secure environment-variable mechanism.

## Prototype limitations

This release is for engineering/prototype testing.

It does not yet include:

- automatic GitHub update manager
- rollback system
- systemd production service
- battery management
- camera live capture pipeline
- voice activity detection
- bone-conduction audio output
