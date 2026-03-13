#!/usr/bin/env python3
"""
Checkers Settings Dialog Tabs

Checkers-specifieke tabs voor settings dialog:
- Gameplay tab: vs_computer, strict_touch_move
- AI tab: Cake configuratie (difficulty, think time)
"""

import pygame
from lib.gui.widgets import UIWidgets

CHECKERS_VARIANT_ITEMS = [
    ('international8', 'International 8x8'),
    ('american',       'American / English'),
    ('russian',        'Russian'),
]


class CheckersSettingsTabs:
    """Checkers-specifieke settings tab renderers"""

    @staticmethod
    def render_gameplay_tab(screen, font_small, dialog_x, content_y, settings, result, gui=None):
        """Render gameplay tab voor checkers"""
        y_pos = content_y
        toggle_x = dialog_x + 50

        # --- Variant dropdown ---
        variant_label = font_small.render("Variant", True, UIWidgets.COLOR_BLACK)
        screen.blit(variant_label, (toggle_x, y_pos + 10))

        current_variant = settings.get('checkers', {}).get('checkers_variant', 'international8')
        variant_display = {v: n for v, n in CHECKERS_VARIANT_ITEMS}.get(current_variant, current_variant)
        is_variant_open = bool(gui and getattr(gui, 'show_checkers_variant_dropdown', False))

        variant_dropdown_rect = UIWidgets.draw_dropdown(
            screen,
            dialog_x + 150,
            y_pos,
            250,
            38,
            variant_display,
            is_variant_open,
            font_small
        )
        result['dropdowns']['checkers_variant'] = variant_dropdown_rect

        if is_variant_open:
            dropdown_items = UIWidgets.draw_dropdown_items(
                screen,
                dialog_x + 150,
                y_pos + 38,
                250,
                36,
                CHECKERS_VARIANT_ITEMS,
                current_variant,
                font_small
            )
            result['dropdown_items'] = dropdown_items

        y_pos += 55

        # Play vs Computer toggle
        vs_computer_toggle = UIWidgets.draw_toggle(
            screen,
            toggle_x,
            y_pos,
            settings.get('checkers', {}).get('play_vs_computer', False),
            font_small
        )
        
        label = font_small.render("Play vs Computer (AI)", True, UIWidgets.COLOR_BLACK)
        screen.blit(label, (vs_computer_toggle.right + 15, y_pos + 8))
        
        result['toggles']['vs_computer_checkers'] = vs_computer_toggle
        
        y_pos += 70
        
        # Strict touch-move toggle
        touch_move_toggle = UIWidgets.draw_toggle(
            screen,
            toggle_x,
            y_pos,
            settings.get('checkers', {}).get('strict_touch_move', False),
            font_small
        )
        
        label = font_small.render("Strict Touch-Move Rule", True, UIWidgets.COLOR_BLACK)
        screen.blit(label, (touch_move_toggle.right + 15, y_pos + 8))
        
        result['toggles']['strict_touch_move_checkers'] = touch_move_toggle
        
        # Info text
        y_pos += 55
        info_text = font_small.render("Strict = must move touched piece", True, (100, 100, 100))
        screen.blit(info_text, (dialog_x + 50, y_pos))
        
        y_pos += 50
        
        # Hide Board Display toggle
        hide_board_toggle = UIWidgets.draw_toggle(
            screen,
            toggle_x,
            y_pos,
            settings.get('checkers', {}).get('hide_board_display', False),
            font_small
        )
        
        label = font_small.render("Hide Board Display", True, UIWidgets.COLOR_BLACK)
        screen.blit(label, (hide_board_toggle.right + 15, y_pos + 8))
        
        result['toggles']['hide_board_display_checkers'] = hide_board_toggle
        
        y_pos += 40
        info_text2 = font_small.render("Hides pieces and highlights on screen", True, (100, 100, 100))
        screen.blit(info_text2, (dialog_x + 50, y_pos))
    
    @staticmethod
    def render_ai_tab(screen, font_small, dialog_x, content_y, settings, result):
        """Render AI tab voor checkers"""
        y_pos = content_y + 20
        label_width = 140
        label_x = dialog_x + 30
        slider_x = label_x + label_width + 20
        slider_width = 200
        
        # Difficulty slider
        diff_label = font_small.render("Difficulty", True, UIWidgets.COLOR_BLACK)
        screen.blit(diff_label, (label_x, y_pos + 8))
        
        difficulty = settings.get('checkers', {}).get('ai_difficulty', 5)
        difficulty_labels = ["Beginner", "Easy", "Medium", "Hard", "Expert"]
        difficulty_idx = min(4, (difficulty - 1) // 2)
        diff_text = f"{difficulty}/10 ({difficulty_labels[difficulty_idx]})"
        
        diff_slider = UIWidgets.draw_slider(
            screen,
            slider_x,
            y_pos,
            slider_width,
            difficulty,
            1,
            10,
            diff_text,
            font_small
        )
        result['sliders']['ai_difficulty'] = diff_slider
        
        y_pos += 50
        
        # Think Time slider
        think_label = font_small.render("Think Time (max)", True, UIWidgets.COLOR_BLACK)
        screen.blit(think_label, (label_x, y_pos + 8))
        
        think_time = settings.get('checkers', {}).get('ai_think_time', 1000)
        
        think_slider = UIWidgets.draw_slider(
            screen,
            slider_x,
            y_pos,
            slider_width,
            think_time,
            500,
            5000,
            f"{think_time} ms",
            font_small
        )
        result['sliders']['ai_think_time'] = think_slider
        
        y_pos += 80
        
        # Info text
        info_text1 = font_small.render("AI Engine Configuration", True, (100, 100, 100))
        screen.blit(info_text1, (dialog_x + 50, y_pos))
        y_pos += 25
        info_text2 = font_small.render("Engine: Built-in heuristic engine", True, (100, 100, 100))
        screen.blit(info_text2, (dialog_x + 50, y_pos))
