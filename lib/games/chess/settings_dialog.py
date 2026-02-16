#!/usr/bin/env python3
"""
Chess Settings Dialog Tabs

Chess-specifieke tabs voor settings dialog:
- Gameplay tab: vs_computer, strict_touch_move
- AI tab: Stockfish configuratie (skill, think time, depth, threads)
"""

from lib.gui.widgets import UIWidgets


class ChessSettingsTabs:
    """Chess-specifieke settings tab renderers"""
    
    @staticmethod
    def render_gameplay_tab(screen, font_small, dialog_x, content_y, settings, result):
        """Render gameplay tab voor chess"""
        y_pos = content_y
        toggle_x = dialog_x + 50
        
        # Play vs Computer toggle
        vs_computer_toggle = UIWidgets.draw_toggle(
            screen,
            toggle_x,
            y_pos,
            settings.get('chess', {}).get('play_vs_computer', False),
            font_small
        )
        
        label = font_small.render("Play vs Computer (Stockfish)", True, UIWidgets.COLOR_BLACK)
        screen.blit(label, (vs_computer_toggle.right + 15, y_pos + 8))
        
        result['toggles']['vs_computer'] = vs_computer_toggle
        
        y_pos += 80
        
        # Strict touch-move toggle
        touch_move_toggle = UIWidgets.draw_toggle(
            screen,
            toggle_x,
            y_pos,
            settings.get('chess', {}).get('strict_touch_move', False),
            font_small
        )
        
        label = font_small.render("Strict Touch-Move Rule", True, UIWidgets.COLOR_BLACK)
        screen.blit(label, (touch_move_toggle.right + 15, y_pos + 8))
        
        result['toggles']['strict_touch_move'] = touch_move_toggle
        
        # Info text
        y_pos += 60
        info_text = font_small.render("Strict = must move touched piece", True, (100, 100, 100))
        screen.blit(info_text, (dialog_x + 50, y_pos))
    
    @staticmethod
    def render_ai_tab(screen, font_small, dialog_x, content_y, settings, result):
        """Render AI (Stockfish) tab voor chess"""
        y_pos = content_y + 20
        label_width = 140
        label_x = dialog_x + 30
        slider_x = label_x + label_width + 20
        slider_width = 200
        
        # Use Worstfish toggle
        worstfish_toggle = UIWidgets.draw_toggle(
            screen,
            label_x,
            y_pos,
            settings.get('chess', {}).get('use_worstfish', False),
            font_small
        )
        
        label = font_small.render("Use Worstfish (weak AI)", True, UIWidgets.COLOR_BLACK)
        screen.blit(label, (worstfish_toggle.right + 15, y_pos + 8))
        
        result['toggles']['use_worstfish'] = worstfish_toggle
        
        y_pos += 60
        
        # Skill Level slider
        skill_label = font_small.render("Skill Level", True, UIWidgets.COLOR_BLACK)
        screen.blit(skill_label, (label_x, y_pos + 8))
        
        skill_level = settings.get('chess', {}).get('stockfish_skill_level', 10)
        difficulty_labels = ["Beginner", "Easy", "Medium", "Hard", "Expert"]
        difficulty_idx = min(4, skill_level // 5)
        skill_text = f"{skill_level}/20 ({difficulty_labels[difficulty_idx]})"
        
        skill_slider = UIWidgets.draw_slider(
            screen,
            slider_x,
            y_pos,
            slider_width,
            skill_level,
            0,
            20,
            skill_text,
            font_small
        )
        result['sliders']['skill'] = skill_slider
        
        y_pos += 50
        
        # Think Time slider
        think_label = font_small.render("Think Time (max)", True, UIWidgets.COLOR_BLACK)
        screen.blit(think_label, (label_x, y_pos + 8))
        
        think_time = settings.get('chess', {}).get('stockfish_think_time', 1000)
        
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
        result['sliders']['think_time'] = think_slider
        
        y_pos += 50
        
        # Search Depth slider
        depth_label = font_small.render("Search Depth", True, UIWidgets.COLOR_BLACK)
        screen.blit(depth_label, (label_x, y_pos + 8))
        
        depth = settings.get('chess', {}).get('stockfish_depth', 15)
        
        depth_slider = UIWidgets.draw_slider(
            screen,
            slider_x,
            y_pos,
            slider_width,
            depth,
            5,
            50,
            f"{depth}",
            font_small
        )
        result['sliders']['depth'] = depth_slider
