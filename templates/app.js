const div = document.getElementById("banner");

    const backgrounds = [
        'url(../static/Image/phoenix/Poster/earbuds-home-banner.jpg)',
        'url(../static/Image/phoenix/Poster/speaker-poster.jpg)'
    ]

    let index = 0;

    function changeBackground(){
        div.style.backgroundImage = backgrounds[index];
        index = (index + 1) % backgrounds.length;
    }

    setInterval(changeBackground, 4000);
    changeBackground();