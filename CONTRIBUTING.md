# Contributing to LincStation S1 LCD & LED Control

Thank you for helping improve this community project.

## Before you start

- Read the README, installation instructions, and safety warnings.
- This project targets the **LincStation S1** and its LCD/LED hardware. Other models may use different interfaces and addresses.
- The project is in a **beta** stage. A complete installation on a second independent S1 has not yet been confirmed.
- Back up your configuration and record the original hardware state before testing changes.

## Reporting a bug

Use the **Bug report** issue template. Include the operating system and version, installation method, relevant commands and logs, and what you expected to happen. Redact passwords, tokens, private IPs if sensitive, serial numbers, and other personal data.

For hardware issues, describe the device model and any confirmed I²C bus/address observations. **Do not run unverified write commands on an I²C device merely to gather information for an issue.**

## Suggesting a feature

Use the **Feature request** issue template and describe the use case, proposed behavior, and hardware/software impact.

## Pull requests

1. Open an issue first for substantial changes so the approach can be discussed.
2. Keep changes focused and explain the hardware and software versions used for testing.
3. Preserve existing working functionality and safety checks; avoid broad changes to I²C access without a documented reason.
4. Update documentation for changed commands, requirements, or behavior.
5. Do not commit credentials, personal data, binary dumps containing secrets, or third-party material without appropriate rights.
6. Submit the pull request using the provided template.

## License

By submitting a contribution, you agree that your contribution may be distributed under the repository's **GNU General Public License v3.0**, subject to any separately identified third-party components and their licenses.
