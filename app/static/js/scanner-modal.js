// Scanner modal para leitura de código de barras
let html5QrCode = null;
let scannerModal = null;
let targetInput = null;

function initScannerModal() {
    // Criar modal se não existir
    if (document.getElementById('scanner-modal')) return;

    const modal = document.createElement('div');
    modal.id = 'scanner-modal';
    modal.className = 'scanner-modal';
    modal.innerHTML = `
        <div class="scanner-modal-content">
            <div class="scanner-modal-header">
                <h3>📷 Escanear código de barras</h3>
                <button type="button" class="scanner-close-btn" onclick="closeScannerModal()">✕</button>
            </div>
            <div class="scanner-modal-body">
                <div id="reader" style="width:100%;max-width:400px;margin:0 auto;"></div>
                <p class="scanner-hint">Aponte a câmera para o código de barras do produto</p>
                <div class="scanner-manual-section">
                    <p>Ou digite manualmente:</p>
                    <div class="scanner-manual-row">
                        <input type="text" id="manual-barcode" placeholder="7891234567890" maxlength="20">
                        <button type="button" class="btn btn-primary" onclick="applyManualBarcode()">OK</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    scannerModal = modal;
}

function openScannerModal(inputId) {
    initScannerModal();
    targetInput = document.getElementById(inputId);
    scannerModal.classList.add('active');
    document.body.style.overflow = 'hidden';

    const reader = document.getElementById('reader');
    reader.innerHTML = '';

    html5QrCode = new Html5Qrcode("reader");

    const config = { 
        fps: 10, 
        qrbox: { width: 250, height: 150 },
        aspectRatio: 1.0
    };

    html5QrCode.start(
        { facingMode: "environment" },
        config,
        (decodedText) => {
            // Sucesso!
            if (targetInput) {
                targetInput.value = decodedText;
                targetInput.dispatchEvent(new Event('input'));
            }
            closeScannerModal();
            showToast('✓ Código detectado: ' + decodedText, 'success');
        },
        (errorMessage) => {
            // Erros de scan são normais, ignorar
        }
    ).catch((err) => {
        console.error("Erro ao iniciar scanner:", err);
        showToast('⚠️ Não foi possível acessar a câmera. Use a digitação manual.', 'warning');
    });
}

function closeScannerModal() {
    if (html5QrCode) {
        html5QrCode.stop().then(() => {
            html5QrCode.clear();
            html5QrCode = null;
        }).catch(() => {
            html5QrCode = null;
        });
    }
    if (scannerModal) {
        scannerModal.classList.remove('active');
    }
    document.body.style.overflow = '';
}

function applyManualBarcode() {
    const manual = document.getElementById('manual-barcode');
    if (manual && manual.value.trim()) {
        if (targetInput) {
            targetInput.value = manual.value.trim();
            targetInput.dispatchEvent(new Event('input'));
        }
        closeScannerModal();
    }
}

// Fechar ao clicar fora
document.addEventListener('click', (e) => {
    if (e.target === scannerModal) {
        closeScannerModal();
    }
});

// Toast helper
function showToast(message, type) {
    const container = document.getElementById('toast-container') || document.body;
    const toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    toast.innerHTML = `<span class="toast-icon">${type === 'success' ? '✓' : '⚠'}</span><span class="toast-message">${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-20px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
