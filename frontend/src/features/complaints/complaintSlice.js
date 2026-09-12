import { createSlice } from "@reduxjs/toolkit";
const initialState = {
  complaint: null,
  messages: [
    {
      role: "ai",
      text: "Ready to assist with complaint intake. Paste complaint text or upload a complaint PDF and I will extract the structured fields.",
    },
  ],
  busy: false,
  error: null,
  tools: null,
  audit: [],
};
const slice = createSlice({
  name: "complaint",
  initialState,
  reducers: {
    setComplaint: (s, a) => {
      s.complaint = a.payload;
    },
    setMessages: (s, a) => {
      s.messages = a.payload;
    },
    addMessage: (s, a) => {
      s.messages.push(a.payload);
    },
    setBusy: (s, a) => {
      s.busy = a.payload;
    },
    setError: (s, a) => {
      s.error = a.payload;
    },
    setTools: (s, a) => {
      s.tools = a.payload;
    },
    setAudit: (s, a) => {
      s.audit = a.payload;
    },
    reset: (s) => Object.assign(s, initialState),
  },
});
export const {
  setComplaint,
  setMessages,
  addMessage,
  setBusy,
  setError,
  setTools,
  setAudit,
  reset,
} = slice.actions;
export default slice.reducer;
