const jogos = [
];

fetch("jogos.json")
    .then(function (resposta) {
        return resposta.json();
    })
    .then(function (catalogo) {
        jogos.push.apply(jogos, catalogo);
        document.dispatchEvent(new Event("jogos-carregados"));
    })
    .catch(function (erro) {
        console.error("Não foi possível carregar o catálogo de jogos:", erro);
    });
