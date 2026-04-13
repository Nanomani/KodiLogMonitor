"""Module containing UI translation strings for multiple languages."""

# Display names shown in the language combo dropdown
LANG_NAMES = {
    "FR": "Français",
    "EN": "English",
    "ES": "Español",
    "DE": "Deutsch",
    "IT": "Italiano",
}

# Reverse mapping: display name → language code
LANG_CODES = {v: k for k, v in LANG_NAMES.items()}

LANGS = {
    "FR": {
        "log": "Ouvrir",
        "sum": "Résumé",
        "exp": "Exporter",
        "upl": "Uploader",
        "clr": "Vider",
        "all": "Tout",
        "debug": "Débogage",
        "info": "Information",
        "warn": "Avertissement",
        "err": "Erreur",
        "ready": "Prêt",
        "sel": "Sélectionnez un fichier LOG.",
        "sys_sum": "\n--- RÉSUMÉ SYSTÈME ---\n",
        "loading": "Chargement...",
        "reset": "\n--- FICHIER RÉINITIALISÉ PAR KODI ---\n",
        "btn_reset": "↻ Réinitialiser",
        "stats_simple": "📈 {} lignes",
        "file_size_text": "📁 {}",
        "limit": "ℹ️ 1000 lignes max",
        "unlimited": "⚠️ Illimité",
        "file_error": "⚠️ LOG INACCESSIBLE",
        "none": "Aucun",
        "paused": "⏸️ En pause",
        "line_break": "↩ Retour à la ligne",
        "warn_title": "Fichier Volumineux",
        "warn_msg": "Le fichier fait {:.1f} Mo.\nLe chargement complet risque de faire planter l'application.\n\nVeuillez consulter le fichier manuellement.",
        "perf_title": "Performance",
        "perf_msg": "Charger le fichier complet pour voir le contexte ?\n(Cela peut être lent sur les gros fichiers)",
        "search_ph": "Rechercher...",
        "filter_applied": "Filtre(s) appliqué(s) :",
        "type_filter": "Type de message",
        "keyword_filter": "Recherche par mot-clé",
        "list_filter": "Recherche par liste",
        "no_match": "❌ Aucun résultat correspondant aux critères sélectionnés",
        "copy": "Copier",
        "sel_all": "Sélectionner tout",
        "search_localy": "Rechercher",
        "search_google": "Rechercher sur Google",
        "paste": "Coller",
        "clear": "Effacer",
        "inactive": "Inactif",
        "t_auto": "Auto",
        "t_light": "Clair",
        "t_dark": "Sombre",
        "win_help_title": "Aide",
        "help_title": "Raccourcis Clavier",
        "no_log": "⚠️ Aucun fichier LOG chargé.",
        "copy_ok": "LOG copié ! Collez-le sur le site.",
        "attn": "Attention",
        "upd_title": "Mise à jour disponible",
        "upd_new_ver": "Nouvelle version disponible :",
        "upd_msg": "Une nouvelle mise à jour a été détectée sur GitHub.\nQue souhaitez-vous faire ?",
        "upd_btn_dl": "Télécharger",
        "upd_btn_skip": "Ignorer",
        "upd_btn_dis": "Désactiver",
        "upd_confirm_title": "Confirmation",
        "upd_confirm_msg": "Désactiver définitivement les notifications de mise à jour ?",
        "already_running": "Une instance de ce programme est déjà en cours d'exécution.",
        "clear_confirm_msg": "Voulez-vous vraiment supprimer tout l'historique de recherche ?",
        "shutdown_confirm_title": "Kodi Log Monitor",
        "shutdown_confirm_msg": (
            "Les paramètres d'affichage de Windows ont changé.\n"
            "Un arrêt est recommandé pour garantir que l'interface s'affiche correctement.\n\n"
            "Cliquez sur Ok pour confirmer\n"
        ),
        "perf_confirm_title": "Avertissement de Performance",
        "perf_confirm_msg": "Ce fichier dépasse 10 Mo ({:.1f} Mo).\nLe charger entièrement risque de dégrader les performances ou figer l'application.\n\nVoulez-vous continuer ?",
        "tip_upd_dl": "Télécharger la mise à jour depuis Github",
        "tip_upd_sk": "Ignorer les notifications pour cette version",
        "tip_upd_di": "Désactiver définitivement les notifications",
        "tip_github": "Ouvrir la page Github",
        "tip_reset": "Réinitialiser filtres et affichage",
        "tip_limit": "Affiche l'intégralité du LOG / limite aux 1000 dernières lignes",
        "tip_wrap": "Retour automatique à la ligne",
        "tip_pause": "Pause / reprise du défilement automatique",
        "tip_help": "Afficher la liste des raccourcis clavier",
        "tip_theme_light":  "Passer au thème clair",
        "tip_theme_dark":   "Passer au thème sombre",
        "theme_close_title": "Thème modifié",
        "theme_close_msg": (
            "Le thème a été modifié.\n\n"
            "L’application va se fermer.\n"
            "Veuillez la relancer pour appliquer le nouveau thème."
        ),
        "display_change_title": "Paramètres d’affichage modifiés",
        "display_change_msg": (
            "Les paramètres d’affichage de Windows ont changé.\n\n"
            "Il est recommandé de fermer l’application\n"
            "afin que l’interface s’adapte correctement au relancement.\n\n"
            "Fermer maintenant ?"
        ),
        "tip_single_instance": "Autoriser plusieurs instances",
        "tip_multi_instance": "Limiter à une seule instance",
        "tip_open": "Ouvrir le fichier LOG",
        "tip_export": (
            "Exporter le résultat du LOG\n"
            "selon vos filtres dans un fichier TXT"
            ),
        "tip_upload": "Ouvrir le service web Paste Kodi",
        "tip_summary": "Afficher les informations système",
        "tip_clear": "Effacer le contenu affiché",
        "tip_down_font": "Réduire la taille du texte",
        "tip_up_font": "Augmenter la taille du texte",
        "tip_kw_refresh": "Actualiser les listes de mots-clés",
        "tip_kw_folder": "Ajouter des listes de mots-clés",
        "tip_filter_all": "Afficher tout le journal",
        "tip_filter_info": "Afficher les messages d’information",
        "tip_filter_warning": "Afficher les avertissements",
        "tip_filter_error": "Afficher les erreurs",
        "tip_filter_debug": "Afficher les messages de débogage",
        "tip_lang": "Choisir la langue de l'interface",
        "tip_search_bar": "Rechercher un mot-clé dans les logs",
        "tip_history_clear": "Supprimer tout l'historique de recherche",
        "tip_kw_list": "Séléctionner une liste de mot à rechercher",
        "help_text": (
            "F1 : Afficher aide\n"
            "↑ ↓ : Défilement du LOG\n"
            "Espace : Pause / Reprise du défilement auto\n"
            "Ctrl + O : Ouvrir un fichier LOG\n"
            "Ctrl + S : Exporter le LOG\n"
            "Ctrl + P : Uploader le LOG\n"
            "Ctrl + F : Rechercher mot clé\n"
            "Ctrl + G : Vider l'affichage de la console\n"
            "Ctrl + L : Retour à la ligne auto\n"
            "Ctrl + T : Mode illimité (∞) / 1000 lignes\n"
            "S : Afficher le résumé système\n"
            "A : Afficher Info, Warn, Error, Debug\n"
            "I, W, E, D : Filtrer Info, Warn, Error ou Debug\n"
            "Ctrl + R : Réinitialiser tous les filtres"
        )
    },
    "EN": {
        "log": "Open",
        "sum": "Summary",
        "exp": "Export",
        "upl": "Upload",
        "clr": "Clear",
        "all": "All",
        "debug": "Debug",
        "info": "Info",
        "warn": "Warning",
        "err": "Error",
        "ready": "Ready",
        "sel": "Select a LOG file.",
        "sys_sum": "\n--- SYSTEM SUMMARY ---\n",
        "loading": "Loading...",
        "reset": "\n--- FILE RESET BY KODI ---\n",
        "btn_reset": "↻ RESET",
        "stats_simple": "📈 {} lines",
        "file_size_text": "📁 {}",
        "limit": "ℹ️ 1000 lines max",
        "unlimited": "⚠️ Unlimited",
        "file_error": "⚠️ LOG UNAVAILABLE",
        "none": "None",
        "paused": "⏸️ Paused",
        "line_break": "↩ Line break",
        "warn_title": "Large File",
        "warn_msg": "The file is {:.1f} MB.\nLoading the full file may crash the application.\n\nPlease check the file manually.",
        "perf_title": "Performance",
        "perf_msg": "Load the full file to see the context?\n(This might be slow on large files)",
        "search_ph": "Search...",
        "filter_applied": "Applied filter(s):",
        "type_filter": "Message type",
        "keyword_filter": "Keyword search",
        "list_filter": "List search",
        "no_match": "❌ No matches found for the selected criteria",
        "copy": "Copy",
        "sel_all": "Select All",
        "search_localy": "Search",
        "search_google": "Search on Google",
        "paste": "Paste",
        "clear": "Clear",
        "inactive": "Inactive",
        "t_auto": "Auto",
        "t_light": "Light",
        "t_dark": "Dark",
        "win_help_title": "Help",
        "help_title": "Keyboard Shortcuts",
        "no_log": "⚠️ No LOG file loaded.",
        "copy_ok": "LOG copied! Paste it on the website.",
        "attn": "Attention",
        "upd_title": "Update Available",
        "upd_new_ver": "New version available:",
        "upd_msg": "A new update has been detected on GitHub.\nWhat would you like to do?",
        "upd_btn_dl": "Download",
        "upd_btn_skip": "Skip",
        "upd_btn_dis": "Disable",
        "upd_confirm_title": "Confirm",
        "upd_confirm_msg": "Disable update notifications permanently?",
        "already_running": "An instance of this program is already running.",
        "clear_confirm_msg": "Do you want to delete all search history?",
        "shutdown_confirm_title": "Kodi Log Monitor",
        "shutdown_confirm_msg": (
            "Windows display settings have changed.\n"
            "A shutdown is recommended to ensure the interface displays correctly.\n\n"
            "Click OK to confirm\n"
        ),
        "perf_confirm_title": "Performance Warning",
        "perf_confirm_msg": "This file is larger than 10 MB ({:.1f} MB).\nLoading it completely may cause performance issues or freezes.\n\nDo you want to proceed?",
        "tip_upd_dl": "Download the update from GitHub",
        "tip_upd_sk": "Ignore notifications for this version",
        "tip_upd_di": "Permanently disable notifications",
        "tip_github": "Open the GitHub page",
        "tip_reset": "Reset filters and display",
        "tip_limit": "Show full LOG / limit to last 1000 lines",
        "tip_wrap": "Toggle word wrap",
        "tip_pause": "Pause / Resume auto-scroll",
        "tip_help": "Show the list of keyboard shortcuts",
        "tip_theme_light":  "Switch to light theme",
        "tip_theme_dark":   "Switch to dark theme",
        "theme_close_title": "Theme changed",
        "theme_close_msg": (
            "The theme has been changed.\n\n"
            "The application will now close.\n"
            "Please relaunch it to apply the new theme."
        ),
        "display_change_title": "Display settings changed",
        "display_change_msg": (
            "The Windows display settings have changed.\n\n"
            "It is recommended to close the application\n"
            "so the interface adapts correctly on next launch.\n\n"
            "Close now?"
        ),
        "tip_single_instance": "Allow multiple instances",
        "tip_multi_instance": "Limit to a single instance",
        "tip_open": "Open the LOG file",
        "tip_export": (
            "Export the LOG result\n"
            "to a TXT file based on your filters"
        ),
        "tip_upload": "Open the Paste Kodi web service",
        "tip_summary": "Show system information",
        "tip_clear": "Clear the displayed content",
        "tip_down_font": "Decrease text size",
        "tip_up_font": "Increase text size",
        "tip_kw_refresh": "Refresh keyword lists",
        "tip_kw_folder": "Add keyword lists",
        "tip_filter_all": "Show all logs",
        "tip_filter_info": "Show information messages",
        "tip_filter_warning": "Show warnings",
        "tip_filter_error": "Show errors",
        "tip_filter_debug": "Show debug messages",
        "tip_lang": "Choose interface language",
        "tip_search_bar": "Search for a keyword in the logs",
        "tip_history_clear": "Delete all search history",
        "tip_kw_list": "Select a list of keywords to search for",
        "help_text": (
            "F1 : Show help\n"
            "↑ ↓ : Scroll LOG\n"
            "Space : Pause / Resume auto-scroll\n"
            "Ctrl + O : Open LOG file\n"
            "Ctrl + S : Export LOG\n"
            "Ctrl + P : Upload LOG\n"
            "Ctrl + F : Search keyword\n"
            "Ctrl + G : Clear console display\n"
            "Ctrl + L : Toggle word wrap\n"
            "Ctrl + T : Unlimited mode (∞) / 1000 lines\n"
            "S : Show system summary\n"
            "A : Show Info, Warn, Error, Debug\n"
            "I, W, E, D : Filter Info, Warn, Error or Debug\n"
            "Ctrl + R : Reset all filters"
        )
    },
    "ES": {
        "log": "Abrir",
        "sum": "Resumen",
        "exp": "Exportar",
        "upl": "Subir",
        "clr": "Limpiar",
        "all": "Todo",
        "debug": "Debug",
        "info": "Info",
        "warn": "Aviso",
        "err": "Error",
        "ready": "Listo",
        "sel": "Seleccione un archivo LOG.",
        "sys_sum": "\n--- RESUMEN DEL SISTEMA ---\n",
        "loading": "Cargando...",
        "reset": "\n--- ARCHIVO REINICIADO POR KODI ---\n",
        "btn_reset": "↻ Restablecer",
        "stats_simple": "📈 {} líneas",
        "file_size_text": "📁 {}",
        "limit": "ℹ️ 1000 líneas máx.",
        "unlimited": "⚠️ Ilimitado",
        "file_error": "⚠️ LOG NO DISPONIBLE",
        "none": "Ninguno",
        "paused": "⏸️ En pausa",
        "line_break": "↩ Salto de línea",
        "warn_title": "Archivo Grande",
        "warn_msg": "El archivo tiene {:.1f} MB.\nCargar el archivo completo peut colapsar la aplicación.\n\nPor favor, consulte el archivo manualmente.",
        "perf_title": "Rendimiento",
        "perf_msg": "¿Cargar el archivo completo para ver el contexto?\n(Puede ser lento)",
        "search_ph": "Buscar...",
        "filter_applied": "Filtro(s) aplicado(s):",
        "type_filter": "Tipo de mensaje",
        "keyword_filter": "Búsqueda por palabra clave",
        "list_filter": "Búsqueda por lista",
        "no_match": "❌ No se encontró ninguna coincidencia",
        "copy": "Copiar",
        "sel_all": "Seleccionar todo",
        "search_localy": "Buscar",
        "search_google": "uscar en Google",
        "paste": "Pegar",
        "clear": "Borrar",
        "inactive": "Inactivo",
        "t_auto": "Auto",
        "t_light": "Claro",
        "t_dark": "Oscuro",
        "win_help_title": "Ayuda",
        "help_title": "Atajos de Teclado",
        "no_log": "⚠️ No se a cargado aucun archivo de LOG.",
        "copy_ok": "¡LOG copiado! Pégalo en el sitio web.",
        "attn": "Atención",
        "upd_title": "Actualización disponible",
        "upd_new_ver": "Nueva versión disponible:",
        "upd_msg": "Se ha detectado una nueva actualización en GitHub.\n¿Qué desea hacer?",
        "upd_btn_dl": "Descargar",
        "upd_btn_skip": "Omitir",
        "upd_btn_dis": "Desactivar",
        "upd_confirm_title": "Confirmar",
        "upd_confirm_msg": "¿Desactivar permanentemente las notificaciones de actualización?",
        "already_running": "Una instancia de este programa ya está en ejecución.",
        "clear_confirm_msg": "¿Desea eliminar todo el historial de búsqueda?",
        "shutdown_confirm_title": "Kodi Log Monitor",
        "shutdown_confirm_msg": (
            "La configuración de pantalla de Windows ha cambiado.\n"
            "Se recomienda un cierre para garantizar que la interfaz se muestre correctamente.\n\n"
            "Haga clic en OK para confirmar\n"
        ),
        "perf_confirm_title": "Advertencia de rendimiento",
        "perf_confirm_msg": "Este archivo supera los 10 MB ({:.1f} MB).\nCargarlo por completo puede causar problemas de rendimiento o bloqueos.\n\n¿Desea continuar?",
        "tip_upd_dl": "Descargar la actualización desde GitHub",
        "tip_upd_sk": "Ignorar notificaciones para esta versión",
        "tip_upd_di": "Desactivar notificaciones permanentemente",
        "tip_github": "Abrir la página de GitHub",
        "tip_reset": "Restablecer filtros y visualización",
        "tip_limit": "Mostrar LOG completo / limitar a las últimas 1000 líneas",
        "tip_wrap": "Ajuste de línea automático",
        "tip_pause": "Pausa / Reanudar desplazamiento automático",
        "tip_help": "Mostrar la lista de atajos de teclado",
        "tip_theme_light":  "Cambiar al tema claro",
        "tip_theme_dark":   "Cambiar al tema oscuro",
        "theme_close_title": "Tema modificado",
        "theme_close_msg": (
            "El tema ha sido modificado.\n\n"
            "La aplicación se cerrará.\n"
            "Vuelva a abrirla para aplicar el nuevo tema."
        ),
        "display_change_title": "Configuración de pantalla modificada",
        "display_change_msg": (
            "La configuración de pantalla de Windows ha cambiado.\n\n"
            "Se recomienda cerrar la aplicación\n"
            "para que la interfaz se adapte correctamente al relanzarla.\n\n"
            "¿Cerrar ahora?"
        ),
        "tip_single_instance": "Permitir múltiples instancias",
        "tip_multi_instance": "Limitar a una sola instancia",
        "tip_open": "Abrir el archivo LOG",
        "tip_export": (
            "Exportar el resultado del LOG\n"
            "a un archivo TXT según sus filtros"
        ),
        "tip_upload": "Abrir el servicio web Paste Kodi",
        "tip_summary": "Mostrar la información del sistema",
        "tip_clear": "Limpiar el contenido mostrado",
        "tip_down_font": "Reducir el tamaño del texto",
        "tip_up_font": "Aumentar el tamaño del texto",
        "tip_kw_refresh": "Actualizar listas de palabras clave",
        "tip_kw_folder": "Añadir listas de palabras clave",
        "tip_filter_all": "Mostrar todo el registro",
        "tip_filter_info": "Mostrar mensajes de información",
        "tip_filter_warning": "Mostrar advertencias",
        "tip_filter_error": "Mostrar errores",
        "tip_filter_debug": "Mostrar mensajes de depuración",
        "tip_lang": "Elegir el idioma de la interfaz",
        "tip_search_bar": "Buscar una palabra clave en los logs",
        "tip_history_clear": "Eliminar todo el historial de búsqueda",
        "tip_kw_list": "Seleccionar una lista de palabras para buscar",
        "help_text": (
            "F1 : Mostrar ayuda\n"
            "↑ ↓ : Desplazamiento del LOG\n"
            "Espacio : Pausa / Reanudar desplazamiento automático\n"
            "Ctrl + O : Abrir archivo de LOG\n"
            "Ctrl + S : Exportar LOG\n"
            "Ctrl + P : Subir LOG\n"
            "Ctrl + F : Buscar palabra clave\n"
            "Ctrl + G : Limpiar pantalla de la consola\n"
            "Ctrl + L : Ajuste de línea automático\n"
            "Ctrl + T : Modo ilimitado (∞) / 1000 líneas\n"
            "S : Mostrar resumen del sistema\n"
            "A : Mostrar Info, Warn, Error, Debug\n"
            "I, W, E, D : Filtrar Info, Warn, Error o Debug\n"
            "Ctrl + R : Restablecer todos los filtros"
        )
    },
    "DE": {
        "log": "Öffnen",
        "sum": "Übersicht",
        "exp": "Exportieren",
        "upl": "Hochladen",
        "clr": "Leeren",
        "all": "Alle",
        "debug": "Debug",
        "info": "Info",
        "warn": "Warnung",
        "err": "Fehler",
        "ready": "Bereit",
        "sel": "Wählen Sie eine LOG-Datei aus.",
        "sys_sum": "\n--- SYSTEMÜBERSICHT ---\n",
        "loading": "Ladevorgang...",
        "reset": "\n--- DATEI VON KODI ZURÜCKGESETZT ---\n",
        "btn_reset": "↻ Zurücksetzen",
        "stats_simple": "📈 {} Zeilen",
        "file_size_text": "📁 {}",
        "limit": "ℹ️ Max. 1000 Zeilen",
        "unlimited": "⚠️ Unbegrenzt",
        "file_error": "⚠️ LOG NICHT VERFÜGBAR",
        "none": "Keine",
        "paused": "⏸️ Pause",
        "line_break": "↩ Zeilenumbruch",
        "warn_title": "Große Datei",
        "warn_msg": "Die Datei ist {:.1f} MB groß.\nDas Laden der vollständigen Datei kann die App zum Absturz bringen.\n\nBitte prüfen Sie die Datei manuell.",
        "perf_title": "Leistung",
        "perf_msg": "Vollständige Datei laden, um Kontext zu sehen?\n(Kann bei großen Dateien langsam sein)",
        "search_ph": "Suchen...",
        "filter_applied": "Angewandte Filter:",
        "type_filter": "Nachrichtentyp",
        "keyword_filter": "Stichwortsuche",
        "list_filter": "Listensuche",
        "no_match": "❌ Keine Übereinstimmungen gefunden",
        "copy": "Kopieren",
        "sel_all": "Alles auswählen",
        "search_localy": "Suchen",
        "search_google": "Auf Google suchen",
        "paste": "Einfügen",
        "clear": "Löschen",
        "inactive": "Inaktiv",
        "t_auto": "Auto",
        "t_light": "Hell",
        "t_dark": "Dunkel",
        "win_help_title": "Hilfe",
        "help_title": "Tastaturkürzel",
        "no_log": "⚠️ Keine Log-Datei geladen.",
        "copy_ok": "LOG kopiert! Füge es auf der Website ein.",
        "attn": "Achtung",
        "upd_title": "Update verfügbar",
        "upd_new_ver": "Neue version verfügbar:",
        "upd_msg": "Ein neues Update wurde auf GitHub gefunden.\nWas möchten Sie tun?",
        "upd_btn_dl": "Herunterladen",
        "upd_btn_skip": "Überspringen",
        "upd_btn_dis": "Deaktivieren",
        "upd_confirm_title": "Bestätigen",
        "upd_confirm_msg": "Update-Benachrichtigungen dauerhaft deaktivieren?",
        "already_running": "Eine Instanz dieses Programms sird bereits ausgeführt.",
        "clear_confirm_msg": "Möchten Sie den gesamten Suchverlauf löschen?",
        "shutdown_confirm_title": "Kodi Log Monitor",
        "shutdown_confirm_msg": (
            "Die Windows-Anzeige-Einstellungen haben sich geändert.\n"
            "Ein Beenden wird empfohlen, um sicherzustellen, dass die Benutzeroberfläche korrekt angezeigt wird.\n\n"
            "Klicken Sie auf OK zum Bestätigen\n"
        ),
        "perf_confirm_title": "Leistungswarnung",
        "perf_confirm_msg": "Diese Datei ist größer als 10 MB ({:.1f} MB).\nDas vollständige Laden kann zu Leistungsproblemen oder zum Einfrieren der Anwendung führen.\n\nMöchten Sie fortfahren?",
        "tip_upd_dl": "Update von GitHub herunterladen",
        "tip_upd_sk": "Benachrichtigungen für diese Version ignorieren",
        "tip_upd_di": "Benachrichtigungen dauerhaft deaktivieren",
        "tip_github": "Die GitHub-Seite öffnen",
        "tip_reset": "Filter und Anzeige zurücksetzen",
        "tip_limit": "Vollständiges LOG anzeigen / auf die letzten 1000 Zeilen begrenzen",
        "tip_wrap": "Automatischer Zeilenumbruch",
        "tip_pause": "Pause / Automatisches Scrollen fortsetzen",
        "tip_help": "Liste der Tastenkombinationen anzeigen",
        "tip_theme_light":  "Zum hellen Design wechseln",
        "tip_theme_dark":   "Zum dunklen Design wechseln",
        "theme_close_title": "Design geändert",
        "theme_close_msg": (
            "Das Design wurde geändert.\n\n"
            "Die Anwendung wird jetzt geschlossen.\n"
            "Bitte starten Sie sie neu, um das neue Design anzuwenden."
        ),
        "display_change_title": "Anzeigeeinstellungen geändert",
        "display_change_msg": (
            "Die Windows-Anzeigeeinstellungen haben sich geändert.\n\n"
            "Es wird empfohlen, die Anwendung zu schließen,\n"
            "damit sich die Oberfläche beim nächsten Start korrekt anpasst.\n\n"
            "Jetzt schließen?"
        ),
        "tip_single_instance": "Mehrere Instanzen erlauben",
        "tip_multi_instance": "Auf eine einzige Instanz beschränken",
        "tip_open": "LOG-Datei öffnen",
        "tip_export": (
            "LOG-Ergebnis basierend auf Filtern\n"
            "in eine TXT-Datei exportieren"
        ),
        "tip_upload": "Paste Kodi Web-Service öffnen",
        "tip_summary": "Systeminformationen anzeigen",
        "tip_clear": "Angezeigten Inhalt löschen",
        "tip_down_font": "Textgröße verkleinern",
        "tip_up_font": "Textgröße vergrößern",
        "tip_kw_refresh": "Stichwortlisten aktualisieren",
        "tip_kw_folder": "Stichwortlisten hinzufügen",
        "tip_filter_all": "Alle Protokolle anzeigen",
        "tip_filter_info": "Informationsmeldungen anzeigen",
        "tip_filter_warning": "Warnungen anzeigen",
        "tip_filter_error": "Fehler anzeigen",
        "tip_filter_debug": "Debug-Meldungen anzeigen",
        "tip_lang": "Sprache de Benutzeroberfläche wählen",
        "tip_search_bar": "Nach einem Stichwort in den Logs suchen",
        "tip_history_clear": "Gesamten Suchverlauf löschen",
        "tip_kw_list": "Eine Liste von Suchbegriffen auswählen",
        "help_text": (
            "F1 : Hilfe anzeigen\n"
            "↑ ↓ : LOG durchsuchen\n"
            "Leertaste : Pause / Automatisches Scrollen fortsetzen\n"
            "Strg + O : Log-Datei öffnen\n"
            "Strg + S : LOG exportieren\n"
            "Ctrl + P : LOG hochladen\n"
            "Strg + F : Stichwort suchen\n"
            "Strg + G : Konsolenanzeige leeren\n"
            "Strg + L : Automatischer Zeilenumbruch\n"
            "Strg + T : Unbegrenzter Modus (∞) / 1000 Zeilen\n"
            "S : Systemübersicht anzeigen\n"
            "A : Info, Warn, Error, Debug anzeigen\n"
            "I, W, E, D : Filter für Info, Warn, Error oder Debug\n"
            "Strg + R : Alle Filter zurücksetzen"
        )
    },
    "IT": {
        "log": "Apri",
        "sum": "Riepilogo",
        "exp": "Esporta",
        "upl": "Carica",
        "clr": "Pulisci",
        "all": "Tutto",
        "debug": "Debug",
        "info": "Info",
        "warn": "Avviso",
        "err": "Errore",
        "ready": "Pronto",
        "sel": "Seleziona un file LOG.",
        "sys_sum": "\n--- RIEPILOGO SISTEMA ---\n",
        "loading": "Caricamento...",
        "reset": "\n--- FILE RESETTATO DA KODI ---\n",
        "btn_reset": "↻ Ripristina",
        "stats_simple": "📈 {} righe",
        "file_size_text": "📁 {}",
        "limit": "ℹ️ 1000 righe max",
        "unlimited": "⚠️ Illimitato",
        "file_error": "⚠️ LOG NON DISPONIBILE",
        "none": "Nessuno",
        "paused": "⏸️ In pausa",
        "line_break": "↩ Interruzione di riga",
        "warn_title": "File di Grandi Dimensioni",
        "warn_msg": "Il file è di {:.1f} MB.\nIl caricamento completo potrebbe causare il crash dell'app.\n\nSi prega di consultare il file manualmente.",
        "perf_title": "Prestazioni",
        "perf_msg": "Caricare il file completo per vedere il contesto?\n(Potrebbe essere lento su file grandi)",
        "search_ph": "Cerca...",
        "filter_applied": "Filtro(i) applicato(i):",
        "type_filter": "Tipo di messaggio",
        "keyword_filter": "Ricerca per parola chiave",
        "list_filter": "Ricerca per elenco",
        "no_match": "❌ Nessuna corrispondenza trovata",
        "copy": "Copia",
        "sel_all": "Seleziona tutto",
        "search_localy": "Cerca",
        "search_google": "Cerca su Google",
        "paste": "Incolla",
        "clear": "Cancella",
        "inactive": "Inattivo",
        "t_auto": "Auto",
        "t_light": "Chiaro",
        "t_dark": "Scuro",
        "win_help_title": "Aiuto",
        "help_title": "Scorciatoie da Tastiera",
        "no_log": "⚠️ Nessun file LOG caricato.",
        "copy_ok": "LOG copiato! Incollalo sul sito web.",
        "attn": "Attenzione",
        "upd_title": "Aggiornamento disponibile",
        "upd_new_ver": "Nuova versione disponibile:",
        "upd_msg": "È stato rilevato un nuovo aggiornamento su GitHub.\nCosa vorresti fare?",
        "upd_btn_dl": "Scarica",
        "upd_btn_skip": "Ignora",
        "upd_btn_dis": "Disattiva",
        "upd_confirm_title": "Conferma",
        "upd_confirm_msg": "Disattivare permanentemente le notifiche di aggiornamento?",
        "already_running": "Un'istanza di questo programma è già in esecuzione.",
        "clear_confirm_msg": "Vuoi cancellare tutta la cronologia delle ricerche?",
        "shutdown_confirm_title": "Kodi Log Monitor",
        "shutdown_confirm_msg": (
            "Le impostazioni di visualizzazione di Windows sono cambiate.\n"
            "Si raccomanda la chiusura per garantire che l'interfaccia venga visualizzata correttamente.\n\n"
            "Clicca su OK per confermare\n"
        ),
        "perf_confirm_title": "Avviso di prestazioni",
        "perf_confirm_msg": "Questo file è più grande di 10 MB ({:.1f} MB).\nCaricarlo completamente potrebbe causare problemi di prestazioni o blocchi dell'applicazione.\n\nVuoi procedere?",
        "tip_upd_dl": "Scarica l'aggiornamento da GitHub",
        "tip_upd_sk": "Ignora le notifiche per questa versione",
        "tip_upd_di": "Disattiva le notifiche in modo permanente",
        "tip_github": "Apri la pagina GitHub",
        "tip_reset": "Ripristina filtri e visualizzazione",
        "tip_limit": "Mostra LOG completo / limita alle ultime 1000 righe",
        "tip_wrap": "A capo automatico",
        "tip_pause": "Pausa / Riprendi scorrimento automatico",
        "tip_help": "Mostra l'elenco delle scorciatoie da tastiera",
        "tip_theme_light":  "Passa al tema chiaro",
        "tip_theme_dark":   "Passa al tema scuro",
        "theme_close_title": "Tema modificato",
        "theme_close_msg": (
            "Il tema è stato modificato.\n\n"
            "L'applicazione si chiuderà.\n"
            "Riavviarla per applicare il nuovo tema."
        ),
        "display_change_title": "Impostazioni schermo modificate",
        "display_change_msg": (
            "Le impostazioni dello schermo di Windows sono cambiate.\n\n"
            "Si consiglia di chiudere l'applicazione\n"
            "affinché l'interfaccia si adatti correttamente al riavvio.\n\n"
            "Chiudere adesso?"
        ),
        "tip_single_instance": "Consenti più istanze",
        "tip_multi_instance": "Limita a una singola istanza",
        "tip_open": "Apri il file LOG",
        "tip_export": (
            "Esporta il risultato del LOG\n"
            "in un file TXT in base ai filtri"
        ),
        "tip_upload": "Apri il servizio web Paste Kodi",
        "tip_summary": "Mostra le informazioni di sistema",
        "tip_clear": "Cancella il contenuto visualizzato",
        "tip_down_font": "Riduci dimensione testo",
        "tip_up_font": "Aumenta dimensione testo",
        "tip_kw_refresh": "Aggiorna elenchi di parole chiave",
        "tip_kw_folder": "Aggiungi elenchi di parole chiave",
        "tip_filter_all": "Mostra tutto il registro",
        "tip_filter_info": "Mostra messaggi informativi",
        "tip_filter_warning": "Mostra avvisi",
        "tip_filter_error": "Mostra errori",
        "tip_filter_debug": "Mostra messaggi di debug",
        "tip_lang": "Scegli la lingua dell'interfaccia",
        "tip_search_bar": "Cerca una parola chiave nei log",
        "tip_history_clear": "Cancella tutta la cronologia delle ricerche",
        "tip_kw_list": "Selezionare un elenco di parole da cercare",
        "help_text": (
            "F1 : Mostra aiuto\n"
            "↑ ↓ : Scorrimento del LOG\n"
            "Spazio : Pausa / Riprendi scorrimento automatico\n"
            "Ctrl + O : Apri file di LOG\n"
            "Ctrl + S : Esporta LOG\n"
            "Ctrl + P : Carica LOG\n"
            "Ctrl + F : Cerca parola chiave\n"
            "Ctrl + G : Pulisci visualizzazione console\n"
            "Ctrl + L : A capo automatico\n"
            "Ctrl + T : Modalità illimitata (∞) / 1000 righe\n"
            "S : Mostra riepilogo sistema\n"
            "A : Mostra Info, Warn, Error, Debug\n"
            "I, W, E, D : Filtra Info, Warn, Error o Debug\n"
            "Ctrl + R : Ripristina tutti i filtri"
        )
    }
}
