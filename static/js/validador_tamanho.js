// static/js/validador_tamanho.js
// Ficheiro adicional para validar o tamanho dos ficheiros no lado do cliente

document.addEventListener('DOMContentLoaded', function() {
    // Procura o formulário de postagem na página da plataforma
    const form = document.querySelector('form[enctype="multipart/form-data"]');
    if (!form) return;

    const inputFile = form.querySelector('input[type="file"]');
    if (!inputFile) return;

    // Definir os limites em Bytes
    const LIMITE_VIDEO = 50 * 1024 * 1024;  // 50 MB para vídeos
    const LIMITE_IMAGEM = 5 * 1024 * 1024;  // 5 MB para imagens

    form.addEventListener('submit', function(e) {
        if (inputFile.files && inputFile.files[0]) {
            const ficheiro = inputFile.files[0];
            const tamanho = ficheiro.size;
            const tipo = ficheiro.type;

            let limiteMaximo = LIMITE_IMAGEM;
            let nomeTipo = "imagem";

            if (tipo.startsWith('video/')) {
                limiteMaximo = LIMITE_VIDEO;
                nomeTipo = "vídeo";
            }

            // Se passar do limite, cancela o envio e avisa o utilizador
            if (tamanho > limiteMaximo) {
                e.preventDefault(); // Para o envio do formulário
                const limiteMb = limiteMaximo / (1024 * 1024);
                alert(`❌ O ${nomeTipo} selecionado é demasiado grande.\n\nO limite máximo para vídeos é de ${limiteMb}MB para garantir o bom funcionamento da rede social.`);
            }
        }
    });
});
