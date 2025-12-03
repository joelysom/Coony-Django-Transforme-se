// js/eventos.js

// Estado inicial da visualização
let visualizacao = "lista"; 

/**
 * Altera o modo de visualização entre 'lista' e 'grade'.
 * Atualiza as classes CSS do container principal e o estilo dos botões (cores).
 * @param {string} tipo - O tipo de visualização ('lista' ou 'grade').
 */
function mudarVisualizacao(tipo) {
    visualizacao = tipo;
    const listaSection = document.getElementById("eventos-lista-grade"); 
    const btnLista = document.getElementById("btn-lista");
    const btnGrade = document.getElementById("btn-grade");

    // Remove as classes de visualização antigas do container
    listaSection.classList.remove("eventos-lista", "eventos-grid");

    if (tipo === "lista") {
        listaSection.classList.add("eventos-lista");
        // Atualiza as cores dos botões
        btnLista.classList.remove("secondary-btn");
        btnLista.classList.add("primary-btn");
        btnGrade.classList.remove("primary-btn");
        btnGrade.classList.add("secondary-btn");
    } else if (tipo === "grade") {
        listaSection.classList.add("eventos-grid");
        // Atualiza as cores dos botões
        btnGrade.classList.remove("secondary-btn");
        btnGrade.classList.add("primary-btn");
        btnLista.classList.remove("primary-btn");
        btnLista.classList.add("secondary-btn");
    }

    // Aplica o filtro para garantir que os cards visíveis tenham o display correto (block)
    filtrarEventos();
}

/**
 * Filtra os cards de evento com base nos inputs de busca e filtros.
 * Garante que o display do card corresponda ao modo de visualização atual.
 */
function filtrarEventos() {
    const busca = document.getElementById("busca").value.toLowerCase();
    const esporte = document.getElementById("filtro-esporte").value;
    const dificuldade = document.getElementById("filtro-dificuldade").value;

    const cards = document.querySelectorAll("#eventos-lista-grade .evento-card"); 
    
    cards.forEach(card => {
        const texto = card.textContent.toLowerCase();
        // Acessa o texto de elementos ocultos (modalidade/nivel) para filtragem
        const modalidade = card.querySelector(".modalidade")?.textContent?.toLowerCase() || ""; 
        const nivel = card.querySelector(".nivel")?.textContent?.toLowerCase() || "";

        const correspondeBusca = texto.includes(busca);
        // Filtro de esporte: 'todos' ou a modalidade contém o valor selecionado
        const correspondeEsporte = esporte === "todos" || modalidade.includes(esporte);
        // Filtro de dificuldade: 'todos' ou o nível contém o valor selecionado
        const correspondeDificuldade = dificuldade === "todos" || nivel.includes(dificuldade);

        if (correspondeBusca && correspondeEsporte && correspondeDificuldade) {
            // Usa "block" para exibir o card, que atende tanto ao layout lista vertical quanto ao grade.
            card.style.display = "block";
        } else {
            // Oculta o card
            card.style.display = "none";
        }
    });
}

// Inicia a visualização no modo lista quando o DOM estiver completamente carregado.
document.addEventListener('DOMContentLoaded', () => {
    // Inicializa o modo lista e aplica as classes de cor corretas
    mudarVisualizacao('lista'); 
});