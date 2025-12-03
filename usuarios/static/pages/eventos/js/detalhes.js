// js/detalhes.js

/**
 * Dados simulados de eventos para demonstração
 * Em uma aplicação real, estes dados viriam de uma API ou banco de dados
 */
const eventosData = {
    'evento-corrida': {
        title: 'Corrida Matinal',
        badge: 'Corrida',
        badgeClass: 'badge-corrida',
        image: 'img/marcozero.png',
        datetime: '22/10/2025 às 06:30',
        location: 'Marco Zero — Recife Antigo',
        difficulty: 'Iniciante (Baixa Intensidade)',
        distance: '5 km',
        participants: '12 / 30 confirmados',
        description: 'Junte-se a nós para uma corrida matinal energizante no histórico Marco Zero do Recife! Começaremos às 6h30 para aproveitar o clima fresco da manhã e as vistas deslumbrantes do Recife Antigo. Evento ideal para iniciantes e corredores experientes que buscam um treino leve e agradável. Água e frutas serão disponibilizadas ao final. Não esqueça seu tênis confortável e venha fazer parte dessa comunidade ativa!',
        organizer: 'Carlos Silva',
        organizerContact: '@carlossilva_run',
        mapUrl: 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d15894.2746107255!2d-34.8782646!3d-8.0631491!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x7ab18a4c3f4e3b1%3A0x9f7e1f6e6f6e6f6e!2sMarco%20Zero%2C%20Recife%20-%20PE!5e0!3m2!1spt-BR!2sbr!4v1700000000000'
    },
    'evento-ciclismo': {
        title: 'Ciclismo na Orla de BV',
        badge: 'Ciclismo',
        badgeClass: 'badge-ciclismo',
        image: 'img/ciclismo.png',
        datetime: '26/10/2025 às 07:00',
        location: 'Boa Viagem — Recife',
        difficulty: 'Moderado (Média Intensidade)',
        distance: '15 km',
        participants: '8 / 20 confirmados',
        description: 'Pedal matinal pela bela orla de Boa Viagem! Um percurso de 15km que combina exercício e paisagens incríveis. Ideal para ciclistas de nível intermediário que buscam um treino estimulante. Traremos suporte técnico básico e pontos de hidratação. Capacete obrigatório!',
        organizer: 'Ana Oliveira',
        organizerContact: '@ana.bike.recife',
        mapUrl: 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d31786.916982555814!2d-34.91831245!3d-8.12925355!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x7ab1f0c42c43b4b%3A0x5e0c6d8b8e8e8e8e!2sBoa%20Viagem%2C%20Recife%20-%20PE!5e0!3m2!1spt-BR!2sbr!4v1700000000000'
    },
    'evento-yoga': {
        title: 'Yoga na Federal',
        badge: 'Yoga',
        badgeClass: 'badge-yoga',
        image: 'img/yoga.png',
        datetime: '28/10/2025 às 08:00',
        location: 'Campus UFPE — Recife',
        difficulty: 'Iniciante (Baixa Intensidade)',
        distance: 'N/A',
        participants: '15 / 25 confirmados',
        description: 'Sessão de Yoga ao ar livre no campus da UFPE. Venha relaxar, alongar e conectar-se consigo mesmo em um ambiente tranquilo e natural. Aula adequada para todos os níveis, desde iniciantes até praticantes avançados. Traga seu tapete de yoga e uma garrafa de água.',
        organizer: 'Marina Costa',
        organizerContact: '@marina.yoga',
        mapUrl: 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3950.4589234!2d-34.9527!3d-8.0537!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x7ab18eb0!2sUFPE%2C%20Recife%20-%20PE!5e0!3m2!1spt-BR!2sbr!4v1700000000000'
    },
    'evento-trilha': {
        title: 'Trilha Brennadis',
        badge: 'Trilha',
        badgeClass: 'badge-trilha',
        image: 'img/trilha.png',
        datetime: '22/10/2025 às 06:30',
        location: 'Oficina Brennand — Recife',
        difficulty: 'Desafiador (Alta Intensidade)',
        distance: '8 km',
        participants: '10 / 15 confirmados',
        description: 'Trilha desafiadora nos arredores da Oficina Brennand. Percurso com subidas e descidas que vão testar seu condicionamento. Para aventureiros experientes! Equipamento de segurança recomendado. Guia especializado incluído.',
        organizer: 'Roberto Santos',
        organizerContact: '@roberto.trails',
        mapUrl: 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3950.789!2d-34.9234!3d-8.0421!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x7ab18d7c!2sOficina%20Brennand%2C%20Recife%20-%20PE!5e0!3m2!1spt-BR!2sbr!4v1700000000000'
    },
    'evento-natacao': {
        title: 'Troféu União das Águas',
        badge: 'Natação',
        badgeClass: 'badge-natacao',
        image: 'img/natacao.png',
        datetime: '26/10/2025 às 07:00',
        location: 'AABB — Recife',
        difficulty: 'Moderado (Média Intensidade)',
        distance: '1.5 km',
        participants: '18 / 40 confirmados',
        description: 'Competição amigável de natação na AABB. Venha testar suas habilidades aquáticas em um ambiente competitivo mas amigável. Várias categorias disponíveis. Medalhas para os vencedores de cada categoria!',
        organizer: 'Julia Mendes',
        organizerContact: '@julia.swim',
        mapUrl: 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3950.567!2d-34.9089!3d-8.0489!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x7ab18c5d!2sAABB%2C%20Recife%20-%20PE!5e0!3m2!1spt-BR!2sbr!4v1700000000000'
    },
    'evento-caminhada': {
        title: 'Caminhada Histórica',
        badge: 'Caminhada',
        badgeClass: 'badge-caminhada',
        image: 'img/passoAlfandega.png',
        datetime: '29/10/2025 às 17:00',
        location: 'Paço Alfândega — Recife Antigo',
        difficulty: 'Iniciante (Baixa Intensidade)',
        distance: '3 km',
        participants: '20 / 35 confirmados',
        description: 'Caminhada cultural pelo centro histórico de Recife. Combine exercício leve com aprendizado sobre a rica história da nossa cidade. Guia turístico incluído. Paradas em pontos históricos importantes. Perfeito para todas as idades!',
        organizer: 'Pedro Alves',
        organizerContact: '@pedro.historico',
        mapUrl: 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3950.234!2d-34.8756!3d-8.0623!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x7ab18a567!2sPa%C3%A7o%20Alf%C3%A2ndega%2C%20Recife%20-%20PE!5e0!3m2!1spt-BR!2sbr!4v1700000000000'
    }
};

/**
 * Carrega os dados do evento baseado no hash da URL
 */
function carregarEvento() {
    // Obtém o identificador do evento da URL (ex: #evento-corrida)
    const hash = window.location.hash.substring(1); // Remove o '#'
    
    // Busca os dados do evento
    const evento = eventosData[hash];
    
    if (evento) {
        // Atualiza a imagem
        document.getElementById('event-image').src = evento.image;
        document.getElementById('event-image').alt = evento.title;
        
        // Atualiza título e badge
        document.getElementById('event-title').textContent = evento.title;
        const badgeElement = document.getElementById('event-badge');
        badgeElement.textContent = evento.badge;
        badgeElement.className = `badge ${evento.badgeClass}`;
        
        // Atualiza informações principais
        document.getElementById('event-datetime').textContent = evento.datetime;
        document.getElementById('event-location').textContent = evento.location;
        document.getElementById('event-difficulty').textContent = evento.difficulty;
        document.getElementById('event-distance').textContent = evento.distance;
        document.getElementById('event-participants').textContent = evento.participants;
        
        // Atualiza descrição
        document.getElementById('event-description').textContent = evento.description;
        
        // Atualiza organizador
        document.getElementById('organizer-name').textContent = evento.organizer;
        document.getElementById('organizer-contact').textContent = evento.organizerContact;
        
        // Atualiza mapa
        document.getElementById('event-map').src = evento.mapUrl;
    } else {
        // Se o evento não for encontrado, redireciona para a listagem
        console.warn('Evento não encontrado:', hash);
        // Opcional: redirecionar para eventos.html
        // window.location.href = 'eventos.html';
    }
}

/**
 * Confirma a presença do usuário no evento
 */
function confirmarPresenca() {
    alert('Presença confirmada! Você receberá mais informações por e-mail.');
    // Aqui você adicionaria a lógica real de confirmação
}

/**
 * Compartilha o evento
 */
function compartilharEvento() {
    const hash = window.location.hash.substring(1);
    const evento = eventosData[hash];
    
    if (evento && navigator.share) {
        // Usa a API de compartilhamento nativa se disponível
        navigator.share({
            title: evento.title,
            text: `Confira este evento: ${evento.title} - ${evento.datetime}`,
            url: window.location.href
        }).catch((error) => console.log('Erro ao compartilhar:', error));
    } else {
        // Fallback: copia o link para a área de transferência
        navigator.clipboard.writeText(window.location.href).then(() => {
            alert('Link do evento copiado para a área de transferência!');
        }).catch((error) => {
            console.log('Erro ao copiar:', error);
            alert('Não foi possível copiar o link.');
        });
    }
}

/**
 * Navega para a página inicial
 */
function irParaHome() {
    window.location.href = 'eventos.html';
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Carrega os dados do evento quando a página carrega
    carregarEvento();
    
    // Adiciona listeners aos botões
    document.getElementById('btn-participar').addEventListener('click', confirmarPresenca);
    document.getElementById('btn-compartilhar').addEventListener('click', compartilharEvento);
    document.querySelector('.home-btn').addEventListener('click', irParaHome);
    
    // Recarrega os dados se o hash da URL mudar
    window.addEventListener('hashchange', carregarEvento);
});
