class Modal {
    constructor(element, config = {}) {
        // Ensure config is always an object and has a backdrop property
        this._element = element;
        this._config = config || {};
        if (typeof this._config.backdrop === 'undefined') {
            this._config.backdrop = true; // or false, as default
        }
    }

    _initializeBackDrop() {
        // No need to check for this._config or backdrop here, already handled in constructor
        this._backdrop = document.createElement('div');
        this._backdrop.classList.add('modal-backdrop');
        this._backdrop.style.cssText = 'position: fixed; top: 0; left: 0; z-index: 1050; background-color: rgba(0, 0, 0, 0.5);';
        this._element.appendChild(this._backdrop);
    }

    show() {
        this._initializeBackDrop();
        this._element.style.cssText = 'position: fixed; top: 0; left: 0; z-index: 1050; background-color: rgba(0, 0, 0, 0.5);';
        this._element.classList.add('modal-open');
    }

    hide() {
        this._element.style.cssText = 'position: fixed; top: 0; left: 0; z-index: 1050; background-color: rgba(0, 0, 0, 0.5);';
        this._element.classList.remove('modal-open');
    }
}

export default Modal;