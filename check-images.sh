#!/bin/bash

echo "=========================================="
echo "  Verificador de Imágenes FireWatch"
echo "=========================================="
echo ""

IMAGES_DIR="assets/images/thermal"
REQUIRED_IMAGES=(
    "dji-interface-split.jpg"
    "thermal-4-views.jpg"
    "thermal-mountain-wide.jpg"
    "drones-forest-fire.jpg"
)

echo "📁 Buscando en: $IMAGES_DIR"
echo ""

MISSING_COUNT=0
FOUND_COUNT=0

for img in "${REQUIRED_IMAGES[@]}"; do
    if [ -f "$IMAGES_DIR/$img" ]; then
        SIZE=$(du -h "$IMAGES_DIR/$img" | cut -f1)
        echo "✅ $img ($SIZE)"
        ((FOUND_COUNT++))
    else
        echo "❌ FALTA: $img"
        ((MISSING_COUNT++))
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Encontradas: $FOUND_COUNT de 4"
echo "Faltantes: $MISSING_COUNT de 4"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $MISSING_COUNT -eq 0 ]; then
    echo "🎉 ¡Todas las imágenes están listas!"
    echo "✨ Abre index-final.html en tu navegador"
else
    echo "⚠️  Faltan $MISSING_COUNT imágenes"
    echo "📖 Lee: assets/images/thermal/SUBIR-IMAGENES.txt"
    echo ""
    echo "Para subir imágenes:"
    echo "  cp /ruta/a/tu/imagen.jpg $IMAGES_DIR/nombre-correcto.jpg"
fi

echo ""
