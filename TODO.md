<--TODO-->

FIXES/CHNAGES:
    Change generated_files path to Documents
    Move gcodePlotter function from process_image to utils
    Fix the qimageToPil so it works properly, get rid of qpixmapToImage2 after
    Write wave output to file

FEATURES:
    SplashScreen //
    fix wave smoothing
    look into descreet cosine sampling
        plot the roundded int on the image canvas, save float to file?
    finish cropping
    dropdown to select processingtype (wave, tsp...) //
    preset/save profile for machine config (eg preset for A4, A3 paper sizes)

OPTIMISATIONS:
    change numpy to lighter alt?
    C/C++ rewrite?
    Cython?
    optimize processing algos
    python -X importtime main.py //
        lazy imports?
    hashmap or precoumputed wave values
