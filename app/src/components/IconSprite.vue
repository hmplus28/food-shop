<template>
  <!-- اسپرایت آیکون‌های SVG (منتقل‌شده از قالب اصلی) -->
  <svg xmlns="http://www.w3.org/2000/svg" style="display:none" aria-hidden="true" focusable="false">
  <symbol id="i-nut" viewBox="0 0 24 24"><path d="M12 2.5c4.6 3.4 7 7.4 7 11.3a7 7 0 1 1-14 0c0-3.9 2.4-7.9 7-11.3z"/></symbol>
  <symbol id="i-cart" viewBox="0 0 24 24"><path d="M7.3 18.5a1.8 1.8 0 1 0 0 3.6 1.8 1.8 0 0 0 0-3.6zm9.4 0a1.8 1.8 0 1 0 0 3.6 1.8 1.8 0 0 0 0-3.6zM3.6 3.2h1.9c.5 0 .9.3 1 .8l.5 2.2m0 0 1.5 7.2c.1.6.6 1 1.2 1h8.6c.6 0 1.1-.4 1.2-1l1.4-6.4c.1-.6-.3-1.2-1-1.2H7z" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
  <symbol id="i-heart" viewBox="0 0 24 24"><path d="M12 20.3S4 15.1 4 9.6C4 6.9 6.1 5 8.5 5c1.4 0 2.7.7 3.5 1.8C12.8 5.7 14.1 5 15.5 5 17.9 5 20 6.9 20 9.6c0 5.5-8 10.7-8 10.7z"/></symbol>
  <symbol id="i-user" viewBox="0 0 24 24"><path d="M12 12a4.2 4.2 0 1 0 0-8.4 4.2 4.2 0 0 0 0 8.4zm0 2.2c-4.4 0-8 2.3-8 5.1V21h16v-1.7c0-2.8-3.6-5.1-8-5.1z"/></symbol>
  <symbol id="i-search" viewBox="0 0 24 24"><path d="M15.8 14.3h-1l-.3-.4a6.8 6.8 0 1 0-1.2 1.2l.4.3v1l4.4 4.4 1.9-1.9-4.2-4.6zm-6.3 0a4.7 4.7 0 1 1 0-9.4 4.7 4.7 0 0 1 0 9.4z"/></symbol>
  <symbol id="i-phone" viewBox="0 0 24 24"><path d="M6.6 10.8a15.6 15.6 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.2.4 2.4.6 3.7.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.4c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.7.1.3 0 .7-.2 1l-2.2 2.1z"/></symbol>
  <symbol id="i-menu" viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h10" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></symbol>
  <symbol id="i-x" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></symbol>
  <symbol id="i-star" viewBox="0 0 24 24"><path d="M12 2.8l2.9 5.8 6.4 1-4.6 4.5 1 6.4-5.7-3-5.7 3 1-6.4L2.7 9.6l6.4-1L12 2.8z"/></symbol>
  <symbol id="i-truck" viewBox="0 0 24 24"><path d="M3 6.5A1.5 1.5 0 0 1 4.5 5H14v11H3V6.5zM14 9h4.2c.4 0 .8.2 1 .5L21.6 13c.2.3.4.7.4 1v2h-8V9zM7 19.4a1.9 1.9 0 1 0 0-3.8 1.9 1.9 0 0 0 0 3.8zm10.5 0a1.9 1.9 0 1 0 0-3.8 1.9 1.9 0 0 0 0 3.8z"/></symbol>
  <symbol id="i-shield" viewBox="0 0 24 24"><path d="M12 2l8 3v6.2c0 5-3.4 9.3-8 10.8-4.6-1.5-8-5.8-8-10.8V5l8-3zm-1.2 13.5l6-6-1.5-1.5-4.5 4.5-2.1-2.1-1.5 1.5 3.6 3.6z"/></symbol>
  <symbol id="i-leaf" viewBox="0 0 24 24"><path d="M20 4c-9 0-15 4.5-15 12 0 .8.1 1.6.3 2.3C7 16 9.6 13.5 13 12c-3 2-5.6 5-6.8 8.2.9.5 2 .8 3.3.8 7.5 0 10.5-7 10.5-17z"/></symbol>
  <symbol id="i-clock" viewBox="0 0 24 24"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm1 5h-2v6l5 3 1-1.7-4-2.3V7z"/></symbol>
  <symbol id="i-gift" viewBox="0 0 24 24"><path d="M20 7h-2.2c.3-.5.5-1.1.5-1.7A2.8 2.8 0 0 0 15.5 2.5c-1.4 0-2.6.8-3.5 2-.9-1.2-2.1-2-3.5-2A2.8 2.8 0 0 0 5.7 5.3c0 .6.2 1.2.5 1.7H4a1.5 1.5 0 0 0-1.5 1.5V11h8V7h3v4h8V8.5A1.5 1.5 0 0 0 20 7zM4 12.5V21h7v-8.5H4zm9 0V21h7v-8.5h-7z"/></symbol>
  <symbol id="i-headset" viewBox="0 0 24 24"><path d="M12 3a9 9 0 0 0-9 9v5a3 3 0 0 0 3 3h2v-8H5.5v-.2A6.7 6.7 0 0 1 12 5.3a6.7 6.7 0 0 1 6.5 6.5v.2H16v8h2a3 3 0 0 0 3-3v-5a9 9 0 0 0-9-9z"/></symbol>
  <symbol id="i-tag" viewBox="0 0 24 24"><path d="M21.4 11.6l-9-9A2 2 0 0 0 11 2H4a2 2 0 0 0-2 2v7c0 .5.2 1 .6 1.4l9 9a2 2 0 0 0 2.8 0l7-7a2 2 0 0 0 0-2.8zM7.5 9A1.5 1.5 0 1 1 9 7.5 1.5 1.5 0 0 1 7.5 9z"/></symbol>
  <symbol id="i-wallet" viewBox="0 0 24 24"><path d="M19 7h-1V6a3 3 0 0 0-3-3H5a3 3 0 0 0-3 3v12a3 3 0 0 0 3 3h14a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2zm-4 8.5a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zM16 7H5V5h11v2z"/></symbol>
  <symbol id="i-pin" viewBox="0 0 24 24"><path d="M12 2a7.4 7.4 0 0 0-7.4 7.4C4.6 14.9 12 22 12 22s7.4-7.1 7.4-12.6A7.4 7.4 0 0 0 12 2zm0 10.1a2.7 2.7 0 1 1 0-5.4 2.7 2.7 0 0 1 0 5.4z"/></symbol>
  <symbol id="i-chev" viewBox="0 0 24 24"><path d="M9.4 6.6L8 8l4 4-4 4 1.4 1.4L14.8 12 9.4 6.6z" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
  <symbol id="i-plus" viewBox="0 0 24 24"><path d="M11 5h2v6h6v2h-6v6h-2v-6H5v-2h6V5z"/></symbol>
  <symbol id="i-minus" viewBox="0 0 24 24"><path d="M5 11h14v2H5z"/></symbol>
  <symbol id="i-trash" viewBox="0 0 24 24"><path d="M9 3h6l1 2h4v2H4V5h4l1-2zM6 9h12l-1 12a2 2 0 0 1-2 1.8H9A2 2 0 0 1 7 21L6 9z"/></symbol>
  <symbol id="i-check" viewBox="0 0 24 24"><path d="M9.6 16.8L5 12.2l-1.4 1.4 6 6 10-10L18.2 8.2 9.6 16.8z"/></symbol>
  <symbol id="i-sms" viewBox="0 0 24 24"><path d="M20 2H4a2 2 0 0 0-2 2v18l4-4h14a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2zM7 9h10v2H7V9zm6 5H7v-2h6v2z"/></symbol>
  <symbol id="i-scale" viewBox="0 0 24 24"><path d="M12 3a2 2 0 0 1 2 2v1h5.2l2.6 8.1c.1.4.2.9.2 1.4a4.5 4.5 0 0 1-9 0c0-.5.1-1 .2-1.4L15.8 8H13v11h3v2H8v-2h3V8H8.2l2.6 6.1c.1.4.2.9.2 1.4a4.5 4.5 0 0 1-9 0c0-.5.1-1 .2-1.4L4.8 6H10V5a2 2 0 0 1 2-2zm-6.5 6.6L4 13h3l-1.5-3.4zm13 0L17 13h3l-1.5-3.4z"/></symbol>
  <symbol id="i-palette" viewBox="0 0 24 24"><path d="M12 2a10 10 0 0 0 0 20c1.4 0 2.3-1.1 2.3-2.3 0-.6-.2-1.1-.6-1.5-.3-.4-.5-.9-.5-1.4 0-1.2 1-2.3 2.3-2.3h2.6c2.1 0 3.9-1.7 3.9-3.8C22 6 17.5 2 12 2zM6.5 12a1.7 1.7 0 1 1 0-3.4 1.7 1.7 0 0 1 0 3.4zm3.4-4.5a1.7 1.7 0 1 1 0-3.4 1.7 1.7 0 0 1 0 3.4zm4.9 0a1.7 1.7 0 1 1 0-3.4 1.7 1.7 0 0 1 0 3.4zm3.4 4.5a1.7 1.7 0 1 1 0-3.4 1.7 1.7 0 0 1 0 3.4z"/></symbol>
  <symbol id="i-instagram" viewBox="0 0 24 24"><path d="M7.5 2h9A5.5 5.5 0 0 1 22 7.5v9A5.5 5.5 0 0 1 16.5 22h-9A5.5 5.5 0 0 1 2 16.5v-9A5.5 5.5 0 0 1 7.5 2zm0 2A3.5 3.5 0 0 0 4 7.5v9A3.5 3.5 0 0 0 7.5 20h9a3.5 3.5 0 0 0 3.5-3.5v-9A3.5 3.5 0 0 0 16.5 4h-9zM12 7a5 5 0 1 1 0 10 5 5 0 0 1 0-10zm0 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6zm5.5-3.2a1.2 1.2 0 1 1 0 2.4 1.2 1.2 0 0 1 0-2.4z"/></symbol>
  <symbol id="i-telegram" viewBox="0 0 24 24"><path d="M21.9 4.3L18.7 19c-.2 1-.9 1.3-1.8.8l-4.9-3.6-2.4 2.3c-.3.3-.5.5-1 .5l.4-5 9.1-8.2c.4-.4-.1-.6-.6-.2L6.3 12.7l-4.8-1.5c-1-.3-1-1 .2-1.5L20.6 2.9c.9-.3 1.6.2 1.3 1.4z"/></symbol>
  <symbol id="i-whatsapp" viewBox="0 0 24 24"><path d="M12 2a9.9 9.9 0 0 0-8.5 15L2 22l5.2-1.4A9.9 9.9 0 1 0 12 2zm5.4 13.9c-.2.7-1.3 1.3-1.9 1.4-.5.1-1.1.1-1.8-.1-.4-.1-1-.3-1.7-.6-3-1.3-4.9-4.3-5-4.5-.2-.2-1.2-1.6-1.2-3s.7-2.1 1-2.4c.2-.3.5-.3.7-.3h.5c.2 0 .4 0 .6.4l.9 2.1c.1.2.1.4 0 .6l-.4.6-.5.5c-.2.2-.3.4-.1.7.2.3.8 1.3 1.7 2.1 1.2 1.1 2.2 1.4 2.5 1.5.3.1.5.1.7-.1l1-1.2c.2-.3.4-.2.7-.1l2.1 1c.3.1.5.2.6.4 0 .1 0 .7-.2 1.4z"/></symbol>
  <symbol id="i-fire" viewBox="0 0 24 24"><path d="M13.5 2s.5 3-1.5 5.5S7 11 7 15a5 5 0 0 0 10 0c0-1.5-.5-3-1.5-4 0 1.5-1 2.5-2 2.5.5-2 .5-5.5 0-7.5-.3-1.5 0-4 0-4z"/></symbol>
  <symbol id="i-box" viewBox="0 0 24 24"><path d="M12 2l9 4.5v11L12 22l-9-4.5v-11L12 2zm0 2.2L5.7 7.3 12 10.4l6.3-3.1L12 4.2zM5 9v7.3l6 3V12L5 9zm14 0l-6 3v7.3l6-3V9z"/></symbol>
  <symbol id="i-refresh" viewBox="0 0 24 24"><path d="M12 4a8 8 0 0 1 7.7 5.9l1.9-.5A10 10 0 0 0 12 2v2zM4.3 14.1A8 8 0 0 1 12 4V2A10 10 0 0 0 2.4 9.6l1.9.5zm15.4-1.2A8 8 0 0 1 12 20v2a10 10 0 0 0 9.6-7.6l-1.9-.5zM2.4 9.6A10 10 0 0 0 12 22v-2a8 8 0 0 1-7.7-5.9l-1.9.5z"/></symbol>
  <symbol id="i-lock" viewBox="0 0 24 24"><path d="M17 9V7A5 5 0 0 0 7 7v2H5v13h14V9h-2zM9 7a3 3 0 0 1 6 0v2H9V7zm4 9.7V19h-2v-2.3a2 2 0 1 1 2 0z"/></symbol>
  <symbol id="i-percent" viewBox="0 0 24 24"><path d="M7.5 3a4.5 4.5 0 1 0 0 9 4.5 4.5 0 0 0 0-9zm0 6.4A1.9 1.9 0 1 1 7.5 5.6a1.9 1.9 0 0 1 0 3.8zM16.5 12a4.5 4.5 0 1 0 0 9 4.5 4.5 0 0 0 0-9zm0 6.4a1.9 1.9 0 1 1 0-3.8 1.9 1.9 0 0 1 0 3.8zM18.6 3.2L20 4.6 5.4 20.8 4 19.4 18.6 3.2z"/></symbol>
  <symbol id="i-doc" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 7V3.5L18.5 9H13zm-6 4h10v2H7v-2zm0 4h10v2H7v-2z"/></symbol>
</svg>
</template>
