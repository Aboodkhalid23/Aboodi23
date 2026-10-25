"""Motion Score: the film's camera and timing as data (stage 2 of the style compiler, docs/COMPILER.md).

    timeexpr  musical, frame-exact times ("B12-2f", "drop+1b", "S+0.25s")
    eases     GSAP names, cubic-bezier, springs → one normalised form
    model     load / validate / resolve (a folder with one file per shot, so parallel builders never collide)
    runtime   evaluate a resolved score (twin of assets/score/score.js, which the engines load)
    transfer  motion transfer: the reference's measured moves → score moves
    predict   what perception will measure for the score's camera, before rendering
"""
