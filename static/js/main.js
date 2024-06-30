document.addEventListener('DOMContentLoaded', function () {
    fetch('/documento')
        .then(response => response.json())
        .then(data => {
            const listaDocumentos = document.getElementById('documentos');
            data.forEach(doc => {
                const item = document.createElement('li');
                item.textContent = doc.DocumentoID + ' - ' + doc.URI;
                listaDocumentos.appendChild(item);
            });
        });
});
