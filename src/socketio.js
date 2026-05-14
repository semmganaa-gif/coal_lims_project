/**
 * Socket.io-client entry — chat WebSocket-д.
 *
 * Ачаалах:
 *   {{ vite_js_tag('src/socketio.js') }}
 *
 * `window.io` глобал API — Flask-SocketIO server-тэй холбогдоход
 * legacy chat.js код-той нийцнэ.
 */

import { io } from 'socket.io-client'

window.io = io

console.log('Socket.io-client v4 bundle loaded')
