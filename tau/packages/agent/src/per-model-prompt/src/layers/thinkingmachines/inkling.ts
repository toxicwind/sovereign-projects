export const INKLING_CODING_AGENT = `
TOOL_DISCIPLINE for thinkingmachines/*:
- Never use echo/bash prose to simulate file creation. Use @oh-my-pi/pi-natives grep/find/read directly.
- One tool call per turn; never chain echo > 5 times.
- Verify with read/grep, not bash echo statements.
VERIFICATION_CONTRACT:
- "really careful" = use native read, not bash verification.
- Never emit raw transcript echoes.
`;
