document.addEventListener('DOMContentLoaded', () => {
    // -----------------------------------------------------------
    // 1. Definição de Variáveis e Elementos DOM
    // -----------------------------------------------------------
    const inputs = document.querySelectorAll('.form-content input, .form-content textarea, .form-content select'); 
    const primaryButton = document.getElementById('btn-primario');
    const requiredInput = document.getElementById('titulo');
    const buttons = document.querySelectorAll('.btn');

    // ELEMENTOS DE CAMPOS PERSONALIZADOS
    const modalidadeSelect = document.getElementById('modalidade'); 
    const campoOutraModalidade = document.getElementById('campo-outra-modalidade');
    const inputOutraModalidade = document.getElementById('modalidadePersonalizada');
    const localSelect = document.getElementById('local'); 
    const campoOutroLocal = document.getElementById('campo-outro-local');
    const inputOutroLocal = document.getElementById('localPersonalizado'); 
    
    // ELEMENTOS PARA UPLOAD DE FOTO
    const fotoInput = document.getElementById('fotoEvento');
    const fotoLabel = document.getElementById('label-foto-evento');
    const nomeArquivoSpan = document.getElementById('nomeArquivo');
    
    // TEXTO ORIGINAL DO LABEL DE FOTO
    const textoLabelOriginal = '📸 Insira aqui a foto do evento (Opcional)';

    // -----------------------------------------------------------
    // 2. Função Genérica para Lógica "Outro (Especifique)"
    // -----------------------------------------------------------
    function togglePersonalizado(selectElement, campoElement, inputElement) {
        if (selectElement.value === 'Outro') {
            campoElement.style.display = 'block'; 
        } else {
            campoElement.style.display = 'none';  
            if (inputElement) {
                inputElement.value = '';
            }
        }
    }
    
    // -----------------------------------------------------------
    // 3. Controle de Foco dos Inputs (Foco e Brilho #EC8441)
    // -----------------------------------------------------------
    inputs.forEach(input => {
        input.addEventListener('focus', () => {
            input.classList.add('input-focus');
        });

        input.addEventListener('blur', () => {
            input.classList.remove('input-focus');
        });
    });
    
    // -----------------------------------------------------------
    // 4. Listeners de Evento para Campos Personalizados
    // -----------------------------------------------------------
    
    // Local
    if (localSelect) {
        localSelect.addEventListener('change', () => {
            togglePersonalizado(localSelect, campoOutroLocal, inputOutroLocal);
        });
        togglePersonalizado(localSelect, campoOutroLocal, inputOutroLocal);
    }
    
    // Modalidade Esportiva
    if (modalidadeSelect) {
        modalidadeSelect.addEventListener('change', () => {
            togglePersonalizado(modalidadeSelect, campoOutraModalidade, inputOutraModalidade);
        });
        togglePersonalizado(modalidadeSelect, campoOutraModalidade, inputOutraModalidade);
    }

    // UPLOAD DE FOTO: Listener para feedback visual
    if (fotoInput) {
        fotoInput.addEventListener('change', () => {
            if (fotoInput.files.length > 0) {
                const nome = fotoInput.files[0].name;
                
                fotoLabel.innerHTML = `✅ <strong>Foto selecionada</strong>: ${nome}`;
                nomeArquivoSpan.textContent = `Arquivo pronto para upload.`;
                nomeArquivoSpan.style.display = 'block';
                
                fotoLabel.style.opacity = '1.0'; 

            } else {
                // Se o usuário cancelar a seleção
                fotoLabel.innerHTML = textoLabelOriginal;
                nomeArquivoSpan.style.display = 'none';
                fotoLabel.style.opacity = '0.7'; 
            }
        });
    }

    // -----------------------------------------------------------
    // 5. Controle do Botão Principal (Desabilitado / Requerimento)
    // -----------------------------------------------------------
    
    const checkRequired = () => {
        if (requiredInput.value.trim() !== '') {
            primaryButton.disabled = false;
        } else {
            primaryButton.disabled = true;
        }
    };

    checkRequired();
    requiredInput.addEventListener('input', checkRequired);


    // -----------------------------------------------------------
    // 6. Feedback Visual e Ações dos Botões
    // -----------------------------------------------------------
    buttons.forEach(button => {
        button.classList.add('btn-active');
    });

    primaryButton.addEventListener('click', (e) => {
        e.preventDefault();
        if (!primaryButton.disabled) {
            alert('Evento Criado! (Ação simulada)');
        }
    });
});
