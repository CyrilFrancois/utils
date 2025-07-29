#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de PDF pour cartes Magic The Gathering
=================================================

Ce script parcourt un dossier d'images et génère un PDF avec des cartes
au format MTG standard (63mm × 88mm) disposées 9 par page (3×3).

Auteur: Assistant IA
Version: 1.0
Python: 3.8+
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Optional
import logging

try:
    from PIL import Image, ImageOps
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.lib.colors import black, lightgrey
except ImportError as e:
    print(f"❌ Erreur d'importation: {e}")
    print("📦 Installez les dépendances avec: pip install pillow reportlab")
    sys.exit(1)

# ============================================================================
# CONFIGURATION - Modifiez ces valeurs selon vos besoins
# ============================================================================

# Dimensions des cartes MTG en mm
CARD_WIDTH_MM = 63
CARD_HEIGHT_MM = 88

# Résolution pour la conversion (300 DPI recommandé pour l'impression)
DPI = 300

# Dimensions en pixels (calculées automatiquement)
CARD_WIDTH_PX = int(CARD_WIDTH_MM * DPI / 25.4)
CARD_HEIGHT_PX = int(CARD_HEIGHT_MM * DPI / 25.4)

# Marges de page en mm
MARGIN_TOP = 5
MARGIN_BOTTOM = 5
MARGIN_LEFT = 5
MARGIN_RIGHT = 5

# Espacement entre cartes en mm
CARD_SPACING_X = 1
CARD_SPACING_Y = 1

# Repères de découpe
ENABLE_CUT_MARKS = False  # Activer/désactiver les repères de découpe
CUT_MARK_COLOR = lightgrey
CUT_MARK_WIDTH = 0.5  # en points

# Extensions d'images supportées
SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg'}

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def find_image_files(source_dir: str) -> List[Path]:
    """
    Parcourt le dossier source et retourne la liste des fichiers d'images valides.
    
    Args:
        source_dir (str): Chemin du dossier à parcourir
        
    Returns:
        List[Path]: Liste des fichiers d'images trouvés
        
    Raises:
        FileNotFoundError: Si le dossier source n'existe pas
    """
    source_path = Path(source_dir)
    
    if not source_path.exists():
        raise FileNotFoundError(f"Le dossier source '{source_dir}' n'existe pas")
    
    if not source_path.is_dir():
        raise NotADirectoryError(f"'{source_dir}' n'est pas un dossier")
    
    image_files = []
    
    # Parcours récursif du dossier
    for file_path in source_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            image_files.append(file_path)
    
    logger.info(f"🔍 Trouvé {len(image_files)} fichier(s) d'image dans '{source_dir}'")
    return sorted(image_files)

def resize_image_to_card(image_path: Path) -> Optional[Image.Image]:
    """
    Redimensionne une image aux dimensions d'une carte MTG en conservant le ratio.
    Ajoute des marges blanches si nécessaire.
    
    Args:
        image_path (Path): Chemin vers l'image à traiter
        
    Returns:
        Optional[Image.Image]: Image redimensionnée ou None si erreur
    """
    try:
        # Ouverture de l'image
        with Image.open(image_path) as img:
            # Conversion en RGB si nécessaire
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Redimensionnement en conservant le ratio
            img_resized = ImageOps.fit(
                img, 
                (CARD_WIDTH_PX, CARD_HEIGHT_PX), 
                Image.Resampling.LANCZOS,
                centering=(0.5, 0.5)
            )
            
            # Création d'une image avec fond blanc
            final_img = Image.new('RGB', (CARD_WIDTH_PX, CARD_HEIGHT_PX), 'white')
            
            # Centrage de l'image redimensionnée
            paste_x = (CARD_WIDTH_PX - img_resized.width) // 2
            paste_y = (CARD_HEIGHT_PX - img_resized.height) // 2
            final_img.paste(img_resized, (paste_x, paste_y))
            
            return final_img
            
    except Exception as e:
        logger.error(f"❌ Erreur lors du traitement de '{image_path}': {e}")
        return None

def calculate_layout() -> Tuple[int, int, float, float]:
    """
    Calcule la disposition des cartes sur la page A4.
    
    Returns:
        Tuple[int, int, float, float]: (cols, rows, start_x, start_y) en mm
    """
    # Dimensions utiles de la page A4
    page_width = A4[0] / mm  # Conversion en mm
    page_height = A4[1] / mm
    
    # Espace disponible après marges
    available_width = page_width - MARGIN_LEFT - MARGIN_RIGHT
    available_height = page_height - MARGIN_TOP - MARGIN_BOTTOM
    
    # Calcul du nombre de colonnes et lignes possibles
    cols = int((available_width + CARD_SPACING_X) / (CARD_WIDTH_MM + CARD_SPACING_X))
    rows = int((available_height + CARD_SPACING_Y) / (CARD_HEIGHT_MM + CARD_SPACING_Y))
    
    # Limitation à 3x3 comme demandé
    cols = min(cols, 3)
    rows = min(rows, 3)
    
    # Calcul de la position de départ pour centrer le contenu
    total_width = cols * CARD_WIDTH_MM + (cols - 1) * CARD_SPACING_X
    total_height = rows * CARD_HEIGHT_MM + (rows - 1) * CARD_SPACING_Y
    
    start_x = MARGIN_LEFT + (available_width - total_width) / 2
    start_y = MARGIN_BOTTOM + (available_height - total_height) / 2
    
    logger.info(f"📐 Disposition: {cols}×{rows} cartes par page")
    return cols, rows, start_x, start_y

def draw_cut_marks(c: canvas.Canvas, x: float, y: float, width: float, height: float):
    """
    Dessine les repères de découpe autour d'une carte.
    
    Args:
        c (canvas.Canvas): Canvas reportlab
        x, y (float): Position de la carte en mm
        width, height (float): Dimensions de la carte en mm
    """
    c.setStrokeColor(CUT_MARK_COLOR)
    c.setLineWidth(CUT_MARK_WIDTH)
    
    # Conversion en points
    x_pt = x * mm
    y_pt = y * mm
    w_pt = width * mm
    h_pt = height * mm
    
    mark_length = 3 * mm  # Longueur des repères
    
    # Repères aux coins
    corners = [
        (x_pt, y_pt),  # Coin bas-gauche
        (x_pt + w_pt, y_pt),  # Coin bas-droit
        (x_pt, y_pt + h_pt),  # Coin haut-gauche
        (x_pt + w_pt, y_pt + h_pt)  # Coin haut-droit
    ]
    
    for corner_x, corner_y in corners:
        # Repère horizontal
        c.line(corner_x - mark_length, corner_y, corner_x + mark_length, corner_y)
        # Repère vertical
        c.line(corner_x, corner_y - mark_length, corner_x, corner_y + mark_length)

def generate_pdf(images: List[Path], output_path: str, preview_only: bool = False):
    """
    Génère le PDF avec les cartes MTG.
    
    Args:
        images (List[Path]): Liste des chemins d'images
        output_path (str): Chemin du fichier PDF de sortie
        preview_only (bool): Si True, génère seulement la première page
    """
    if not images:
        logger.warning("⚠️ Aucune image à traiter")
        return
    
    # Calcul de la disposition
    cols, rows, start_x, start_y = calculate_layout()
    cards_per_page = cols * rows
    
    # Création du PDF
    c = canvas.Canvas(output_path, pagesize=A4)
    
    # Métadonnées
    c.setTitle("Cartes Magic The Gathering")
    c.setAuthor("MTG PDF Generator")
    c.setSubject("Impression de cartes MTG")
    
    processed_images = 0
    current_page = 1
    
    # Traitement des images par lots
    for i in range(0, len(images), cards_per_page):
        if preview_only and current_page > 1:
            break
            
        batch = images[i:i + cards_per_page]
        logger.info(f"📄 Génération de la page {current_page}...")
        
        # Traitement de chaque image du lot
        for j, image_path in enumerate(batch):
            # Calcul de la position sur la grille
            col = j % cols
            row = j // cols
            
            # Position en mm
            x = start_x + col * (CARD_WIDTH_MM + CARD_SPACING_X)
            y = start_y + (rows - 1 - row) * (CARD_HEIGHT_MM + CARD_SPACING_Y)
            
            # Redimensionnement de l'image
            processed_img = resize_image_to_card(image_path)
            if processed_img is None:
                continue
            
            # Sauvegarde temporaire de l'image (avec index global unique)
            temp_path = f"temp_card_{i+j}.png"
            processed_img.save(temp_path, "PNG", dpi=(DPI, DPI))
            
            try:
                # Insertion de l'image dans le PDF
                c.drawImage(
                    temp_path,
                    x * mm,
                    y * mm,
                    width=CARD_WIDTH_MM * mm,
                    height=CARD_HEIGHT_MM * mm,
                    preserveAspectRatio=True
                )
                
                # Ajout des repères de découpe (si activés)
                if ENABLE_CUT_MARKS:
                    draw_cut_marks(c, x, y, CARD_WIDTH_MM, CARD_HEIGHT_MM)
                
                processed_images += 1
                
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'insertion de '{image_path}': {e}")
            
            finally:
                # Suppression du fichier temporaire
                try:
                    os.remove(temp_path)
                except:
                    pass
        
        # Finalisation de la page
        c.showPage()
        current_page += 1
    
    # Sauvegarde du PDF
    c.save()
    
    logger.info(f"✅ PDF généré: '{output_path}'")
    logger.info(f"📊 {processed_images} cartes traitées sur {len(images)} images")

# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

def main():
    """Fonction principale du script."""
    parser = argparse.ArgumentParser(
        description="Générateur de PDF pour cartes Magic The Gathering",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python generate_mtg_pdf.py --source_dir="C:\\MesCartes" --output="mescartes.pdf"
  python generate_mtg_pdf.py --source_dir="./images" --output="preview.pdf" --preview
  python generate_mtg_pdf.py --source_dir="./images" --no-cut-marks
        """
    )
    
    parser.add_argument(
        '--source_dir',
        type=str,
        default='./images',
        help='Dossier contenant les images (défaut: ./images)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='mtg_cards.pdf',
        help='Nom du fichier PDF de sortie (défaut: mtg_cards.pdf)'
    )
    
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Génère seulement la première page (aperçu)'
    )
    
    parser.add_argument(
        '--no-cut-marks',
        action='store_true',
        help='Désactive les repères de découpe'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Affichage détaillé'
    )
    
    args = parser.parse_args()
    
    # Configuration du logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Configuration des repères de découpe
    global ENABLE_CUT_MARKS
    if args.no_cut_marks:
        ENABLE_CUT_MARKS = False
    
    try:
        logger.info("🚀 Démarrage du générateur de PDF MTG")
        
        # Recherche des images
        image_files = find_image_files(args.source_dir)
        
        if not image_files:
            logger.warning("⚠️ Aucune image trouvée dans le dossier spécifié")
            return
        
        # Génération du PDF
        generate_pdf(image_files, args.output, args.preview)
        
        logger.info("🎉 Génération terminée avec succès!")
        
    except Exception as e:
        logger.error(f"💥 Erreur fatale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()