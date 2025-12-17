/**
 * serial_balance.js
 *
 * Mettler Toledo жинтэй Web Serial API-р холбогдох модуль.
 * Coal LIMS системд зориулав.
 *
 * Дэмжигдсэн жингүүд:
 * - Mettler Toledo (MS, ME, ML, XS series)
 * - Sartorius (Entris, Quintix)
 * - AND (GX, GF series)
 *
 * Ашиглах жишээ:
 *   await labBalance.connect();
 *   const weight = await labBalance.getStableWeight();
 *
 * @author Coal LIMS Team
 * @version 1.0.0
 * @date 2025-12-17
 */

class SerialBalance {
    constructor() {
        this.port = null;
        this.isConnected = false;
        this.reader = null;
        this.writer = null;

        // Тохиргоо (Mettler Toledo default)
        this.config = {
            baudRate: 9600,
            dataBits: 8,
            stopBits: 1,
            parity: "none",
            flowControl: "none"
        };

        // Командууд (Mettler MT-SICS protocol)
        this.commands = {
            STABLE: "S\r\n",      // Тогтвортой жин авах
            IMMEDIATE: "SI\r\n",  // Шууд жин авах (тогтворгүй ч гэсэн)
            ZERO: "Z\r\n",        // Тэг болгох (Tare)
            TARE: "T\r\n",        // Tare
            INFO: "I1\r\n"        // Жингийн мэдээлэл
        };

        // Callback-ууд
        this.onConnect = null;
        this.onDisconnect = null;
        this.onWeightReceived = null;
        this.onError = null;
        this.onStatusChange = null;
    }

    /**
     * Web Serial API дэмжигдэж байгаа эсэхийг шалгах
     */
    isSupported() {
        return "serial" in navigator;
    }

    /**
     * Жинтэй холбогдох
     * @returns {Promise<boolean>}
     */
    async connect() {
        if (!this.isSupported()) {
            this._emitError("Web Serial API дэмжигдэхгүй байна. Chrome 89+ ашиглана уу.");
            return false;
        }

        try {
            this._emitStatus("Жин сонгож байна...");

            // Хэрэглэгчээс порт сонгуулах
            this.port = await navigator.serial.requestPort();

            this._emitStatus("Холбогдож байна...");

            // Порт нээх
            await this.port.open(this.config);

            this.isConnected = true;
            this._emitStatus("Холбогдлоо");

            if (this.onConnect) {
                this.onConnect();
            }

            // Disconnect event listener
            this.port.addEventListener('disconnect', () => {
                this._handleDisconnect();
            });

            return true;

        } catch (err) {
            console.error("Balance connect error:", err);

            if (err.name === 'NotFoundError') {
                this._emitError("Жин сонгогдоогүй байна.");
            } else if (err.name === 'SecurityError') {
                this._emitError("Хандах эрх байхгүй байна.");
            } else {
                this._emitError(`Холбогдож чадсангүй: ${err.message}`);
            }

            return false;
        }
    }

    /**
     * Тогтвортой жин авах (S команд)
     * @param {number} timeout - Хүлээх хугацаа (ms)
     * @returns {Promise<number|null>}
     */
    async getStableWeight(timeout = 10000) {
        return this._sendCommandAndRead(this.commands.STABLE, timeout);
    }

    /**
     * Шууд жин авах (SI команд) - тогтворгүй ч гэсэн
     * @returns {Promise<number|null>}
     */
    async getImmediateWeight() {
        return this._sendCommandAndRead(this.commands.IMMEDIATE, 3000);
    }

    /**
     * Жинг тэглэх (Zero/Tare)
     * @returns {Promise<boolean>}
     */
    async tare() {
        try {
            await this._sendCommand(this.commands.TARE);
            this._emitStatus("Tare хийгдлээ");
            return true;
        } catch (err) {
            this._emitError("Tare хийж чадсангүй");
            return false;
        }
    }

    /**
     * Холболт салгах
     */
    async disconnect() {
        try {
            if (this.reader) {
                await this.reader.cancel();
                this.reader.releaseLock();
                this.reader = null;
            }

            if (this.port) {
                await this.port.close();
                this.port = null;
            }

            this._handleDisconnect();

        } catch (err) {
            console.error("Disconnect error:", err);
        }
    }

    /**
     * Команд илгээж хариу унших
     * @private
     */
    async _sendCommandAndRead(command, timeout = 10000) {
        if (!this.isConnected || !this.port) {
            this._emitError("Жин холбогдоогүй байна");
            return null;
        }

        try {
            this._emitStatus("Жин тогтворжихыг хүлээж байна...");

            // Команд илгээх
            await this._sendCommand(command);

            // Хариу унших
            const response = await this._readResponse(timeout);

            if (!response) {
                this._emitError("Жингээс хариу ирсэнгүй");
                return null;
            }

            // Хариуг задлах
            const weight = this._parseResponse(response);

            if (weight !== null) {
                this._emitStatus(`Жин: ${weight.toFixed(4)} g`);

                if (this.onWeightReceived) {
                    this.onWeightReceived(weight);
                }
            }

            return weight;

        } catch (err) {
            console.error("Read weight error:", err);
            this._emitError(`Алдаа: ${err.message}`);
            return null;
        }
    }

    /**
     * Команд илгээх
     * @private
     */
    async _sendCommand(command) {
        const writer = this.port.writable.getWriter();
        try {
            const encoder = new TextEncoder();
            await writer.write(encoder.encode(command));
        } finally {
            writer.releaseLock();
        }
    }

    /**
     * Хариу унших
     * @private
     */
    async _readResponse(timeout) {
        const reader = this.port.readable.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        try {
            const startTime = Date.now();

            while (Date.now() - startTime < timeout) {
                const { value, done } = await Promise.race([
                    reader.read(),
                    new Promise((_, reject) =>
                        setTimeout(() => reject(new Error("Timeout")), timeout)
                    )
                ]);

                if (done) break;

                if (value) {
                    buffer += decoder.decode(value);

                    // Мөр төгссөн эсэх шалгах
                    if (buffer.includes("\r\n") || buffer.includes("\n")) {
                        return buffer;
                    }
                }
            }

            return buffer || null;

        } catch (err) {
            if (err.message === "Timeout") {
                return buffer || null;
            }
            throw err;
        } finally {
            reader.releaseLock();
        }
    }

    /**
     * Жингийн хариуг задлах
     * Mettler format: "S S      12.3456 g"
     *                 "S D      12.3456 g" (Dynamic)
     *                 "S I      12.3456 g" (Immediate)
     * @private
     */
    _parseResponse(response) {
        if (!response) return null;

        // Олон төрлийн формат дэмжих
        const patterns = [
            // Mettler: "S S      12.3456 g"
            /S\s+[SDI]\s+(-?\d+\.?\d*)\s*g/i,
            // Sartorius: "  12.3456 g"
            /^\s*(-?\d+\.?\d*)\s*g/im,
            // AND: "ST,+  12.3456  g"
            /[SU]T,\s*[+-]?\s*(-?\d+\.?\d*)\s*g/i,
            // Ерөнхий тоон формат
            /(-?\d+\.\d{2,6})/
        ];

        for (const pattern of patterns) {
            const match = response.match(pattern);
            if (match && match[1]) {
                const weight = parseFloat(match[1]);
                if (!isNaN(weight) && isFinite(weight)) {
                    return weight;
                }
            }
        }

        console.warn("Could not parse weight response:", response);
        return null;
    }

    /**
     * Холболт салсан үед
     * @private
     */
    _handleDisconnect() {
        this.isConnected = false;
        this.port = null;
        this._emitStatus("Холболт салсан");

        if (this.onDisconnect) {
            this.onDisconnect();
        }
    }

    /**
     * Алдаа мэдээлэх
     * @private
     */
    _emitError(message) {
        console.error("Balance error:", message);

        if (this.onError) {
            this.onError(message);
        }

        this._emitStatus(message);
    }

    /**
     * Төлөв мэдээлэх
     * @private
     */
    _emitStatus(message) {
        if (this.onStatusChange) {
            this.onStatusChange(message);
        }
    }
}

// ============================================
// AG-GRID INTEGRATION HELPER
// ============================================

class BalanceGridIntegration {
    constructor(balance) {
        this.balance = balance;
        this.gridApi = null;
        this.weightColumnField = 'weight';
        this.activeCell = null;
    }

    /**
     * AG-Grid API-тай холбох
     */
    setGridApi(api) {
        this.gridApi = api;
    }

    /**
     * Идэвхтэй нүдэнд жин оруулах
     */
    async fillActiveCell() {
        if (!this.gridApi || !this.balance.isConnected) {
            return false;
        }

        const focusedCell = this.gridApi.getFocusedCell();
        if (!focusedCell || focusedCell.column.getColId() !== this.weightColumnField) {
            console.log("Weight column is not focused");
            return false;
        }

        const weight = await this.balance.getStableWeight();

        if (weight !== null) {
            const rowNode = this.gridApi.getDisplayedRowAtIndex(focusedCell.rowIndex);
            if (rowNode) {
                rowNode.setDataValue(this.weightColumnField, weight);

                // Дараагийн мөр рүү үсрэх
                const nextRowIndex = focusedCell.rowIndex + 1;
                const nextRow = this.gridApi.getDisplayedRowAtIndex(nextRowIndex);
                if (nextRow) {
                    this.gridApi.setFocusedCell(nextRowIndex, this.weightColumnField);
                }

                return true;
            }
        }

        return false;
    }
}

// ============================================
// GLOBAL INSTANCE
// ============================================

window.labBalance = new SerialBalance();
window.BalanceGridIntegration = BalanceGridIntegration;

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SerialBalance, BalanceGridIntegration };
}
