#!/bin/bash

# Script para mover la landing page de FireWatch Chile al repositorio prueba
# Ejecuta este script desde tu terminal local

echo "🔥 FireWatch Chile - Mover al repositorio prueba"
echo "================================================"
echo ""

# Verificar que estamos en la branch correcta
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "claude/climate-tech-landing-page-DamDK" ]; then
    echo "❌ No estás en la branch correcta"
    echo "Branch actual: $CURRENT_BRANCH"
    echo "Cambiando a la branch correcta..."
    git checkout claude/climate-tech-landing-page-DamDK
fi

echo "✅ Branch: claude/climate-tech-landing-page-DamDK"
echo ""

# Agregar remote del repo prueba si no existe
if ! git remote | grep -q "^prueba$"; then
    echo "📡 Agregando remote 'prueba'..."
    git remote add prueba https://github.com/d1egol/prueba.git
    echo "✅ Remote agregado"
else
    echo "✅ Remote 'prueba' ya existe"
fi

echo ""
echo "Remotes configurados:"
git remote -v
echo ""

# Hacer push al repo prueba
echo "🚀 Haciendo push a https://github.com/d1egol/prueba..."
echo ""

# Opción 1: Push a main (sobrescribe)
read -p "¿Quieres pushear como rama 'main' en prueba? (s/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo "Pusheando a main..."
    git push prueba claude/climate-tech-landing-page-DamDK:main -f
else
    # Opción 2: Push manteniendo el nombre de la branch
    echo "Pusheando como branch separada..."
    git push prueba claude/climate-tech-landing-page-DamDK
fi

echo ""
echo "✅ ¡Completado!"
echo ""
echo "📋 Próximos pasos:"
echo "1. Visita: https://github.com/d1egol/prueba"
echo "2. Verifica que los archivos estén allí"
echo "3. Abre firewatch-preview.html con:"
echo "   https://htmlpreview.github.io/?https://github.com/d1egol/prueba/blob/main/firewatch-preview.html"
echo ""
