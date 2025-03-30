AV1GUI est une interface graphique (GUI) pour l'encodeur vidéo SVT-AV1 d'apres leur githlab permettant aux utilisateurs de convertir facilement des vidéos en utilisant le codec AV1. 
Cette application permet de spécifier la résolution et forcer le 10 bits, tout en fournissant un retour d'information visuel avec des paramètres bien définis 

Avant d'exécuter cette application, assurez-vous que les éléments suivants sont installés sur votre système :

    Python 3.6+ : AV1GUI est écrit en Python, donc vous devez avoir Python 3.6 ou une version supérieure installée.

    PyQt6 : La bibliothèque d'interface graphique utilisée pour construire l'application.

    FFmpeg : Un outil en ligne de commande pour la conversion de vidéos. Il est utilisé pour extraire les informations vidéo et pour la conversion en format YUV avant l'encodage avec SVT-AV1.

    SVT-AV1 Encoder (SvtAv1EncApp.exe) : L'encodeur vidéo SVT-AV1 pour effectuer l'encodage AV1.

Dépendances

    pip install -r requirements.txt

Utilisation

Lancer l'application

    Exécutez l'application via le script principal :

python av1gui.py   

L'interface graphique s'ouvrira. Vous pourrez : ATTENTION LE PROGRAMME FAIT UN YUV ASSEZ GROS ASSUREZ VOUS D'AVOIR LA PLACE PUIS IL EST SUPPRIMé

    Sélectionner un fichier vidéo (formats supportés : .mp4, .mkv, .avi, .mov). par exemple video.mkv etc

    Spécifier la qualité d'encodage (valeur entre 1 et 63, où 1 est la meilleure qualité).

    Choisir la résolution de la vidéo encodée (par exemple, 1920x1080). sa doit etre la même que la resolution en entrée (source)

    Lancer l'encodage

 Une fois l'encodage terminé, le fichier de sortie sera disponible dans le même répertoire que le fichier source, avec le suffixe _av1.ivf   
