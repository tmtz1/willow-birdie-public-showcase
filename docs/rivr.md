# RIVR

## Plain-language overview

RIVR explores recordings containing sensor streams: images, position data and 3D point clouds. Its goal is to help a researcher inventory what was captured, line streams up in time and inspect them without altering the source files.

Here, ROVR/LightCone names the proprietary recording ecosystem under study. **RTCM** is a satellite-navigation correction-message format; **PCD** stores 3D point-cloud data; **GNSS** means satellite positioning; **IMU** measures motion. A claimed parser capability is not proof that every recording variant is understood.

## ROVR / LightCone research toolkit

RIVR is a personal, local-first research project by Tmtz. It explores unsupported proprietary ROVR LightCone data and provides repeatable, read-only inspection and viewing workflows.

The project is concerned with understanding difficult digital artifacts without altering the source capture. It is not presented as a legal or workplace forensic tool.

## Capabilities represented in the private implementation

- Streaming file inspection with hashes, magic-byte, and entropy reporting
- Dataset inventory, timeline, and sequence-completeness exports
- PCAP/PCAPNG and RoboSense M1P signature scanning
- RTCM3 framing, CRC-24Q validation, and message summaries
- Encrypted-header correlation reports
- Separate-output handling for authorized ROVR decryption workflows
- Synchronized indexing across PCD, camera, depth, GNSS pose, annotations, and nearby IMU samples
- A local viewer with timeline controls, camera/depth imagery, interactive ASCII PCD rendering, and a network-free GNSS path plot

## Research focus

The work examines ROVR `.data` containers, wrapper profiles, RTCM streams, `.gga` classification, inventory, and LiDAR-related references. Large datasets and generated output remain outside version control.

## Safety and privacy boundary

RIVR is designed for local processing. Source captures and generated reports are not published in this showcase. The public repository contains no capture data, encryption keys, or proprietary source code.

## Status

Status clarified September 24, 2026 from the existing public case study; the private implementation was not rerun. In development / research. Encrypted capture recovery is currently parked where the required device key is unavailable. The next research milestone is detection and segmentation annotation overlays.

## Related work

The implementation repository is private: [tmtz1/RIVR](https://github.com/tmtz1/RIVR).
