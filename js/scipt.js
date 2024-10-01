function search() {
    const query = document.getElementById('searchInput').value.toLowerCase().trim();
    const formattedQuery = query.replace(/\s+/g, '-');
    const pageUrl = '/contenu/' + formattedQuery + '.html';

    // Redirection vers la page du contenu
    window.location.href = pageUrl;
}
