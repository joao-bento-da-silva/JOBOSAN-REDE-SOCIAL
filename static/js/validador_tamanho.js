// static/js/validador_tamanho.js
// Ficheiro adicional para validar o tamanho dos ficheiros e links na rede social

document.addEventListener('DOMContentLoaded', function() {
    // Procura por formulários na página da plataforma
    const form = document.querySelector('form');
    if (!form) return;

    // Se houver um input de ficheiro tradicional
    const inputFile = form.querySelector('input[type="file"]');
    
    // Se houver um input de link de mídia (como o usado no código atual da rede social)
    const inputMediaUrl = form.querySelector('input[name="midia_url"]');

    // Definir os limites em Bytes (50MB para vídeos / 5MB para imagens)
    const LIMITE_VIDEO = 50 * 1024 * 1024;  
    const LIMITE_IMAGEM = 5 * 1024 * 1024;  

    form.addEventListener('submit', function(e) {
        // Validação caso utilizem upload físico de ficheiro
        if (inputFile && inputFile.files && inputFile.files[0]) {
            const ficheiro = inputFile.files[0];
            const tamanho = ficheiro.size;
            const tipo = ficheiro.type;

            let limiteMaximo = LIMITE_IMAGEM;
            let nomeTipo = "imagem";

            if (tipo.startsWith('video/')) {
                limiteMaximo = LIMITE_VIDEO;
                nomeTipo = "vídeo";
            }

            if (tamanho > limiteMaximo) {
                e.preventDefault();
                const limiteMb = limiteMaximo / (1024 * 1024);
                alert(`❌ O ${nomeTipo} selecionado excede o tamanho permitido.\n\nO limite máximo é de ${limiteMb}MB.`);
                return;
            }
        }

        // Validação preventiva opcional para URLs diretas (Cloudinary / Links externos)
        if (inputMediaUrl && inputMediaUrl.value.trim() !== "") {
            const url = inputMediaUrl.value.trim().toLowerCase();
            // Apenas um aviso amigável se detetar extensões muito pesadas em links diretos óbvios
            if (url.endsWith('.mp4') || url.endsWith('.mov') || url.endsWith('.avi')) {
                // Mantém o fluxo fluido, pois o servidor Cloudinary já fará a gestão do peso real.
            }
        }
    });
});
