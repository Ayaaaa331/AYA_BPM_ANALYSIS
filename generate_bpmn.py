"""
Generates BPMN-style process flow diagrams for domestic and international
declaration processes. Output: results/domestic_bpmn.png and results/international_bpmn.png
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

OUT = os.path.join(os.path.dirname(__file__), 'results')

TASK_FC   = '#D5E8F0'
TASK_EC   = '#2E5496'
GW_FC     = '#FFF2CC'
GW_EC     = '#D6B656'
LANE_FC   = '#F2F7FC'
LANE_EC   = '#A0AABB'
TEXT_DARK = '#1F3864'
TEXT_GREY = '#555555'
REJ_COLOR = '#C0392B'

def task_box(ax, cx, cy, label, w=3.0, h=0.55, fc=TASK_FC, ec=TASK_EC, fontsize=8.5):
    r = mpatches.FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                                 boxstyle='round,pad=0.05',
                                 facecolor=fc, edgecolor=ec, linewidth=1.5, zorder=4)
    ax.add_patch(r)
    ax.text(cx, cy, label, ha='center', va='center', fontsize=fontsize,
            color=TEXT_DARK, fontweight='bold', zorder=5,
            multialignment='center', linespacing=1.25)

def gateway(ax, cx, cy, label='X', size=0.28):
    pts = np.array([[cx, cy+size], [cx+size*1.5, cy],
                    [cx, cy-size], [cx-size*1.5, cy]])
    poly = mpatches.Polygon(pts, facecolor=GW_FC, edgecolor=GW_EC,
                             linewidth=1.5, zorder=4)
    ax.add_patch(poly)
    ax.text(cx, cy, label, ha='center', va='center',
            fontsize=7, color=TEXT_DARK, fontweight='bold', zorder=5)

def start_evt(ax, cx, cy, r=0.20):
    c = plt.Circle((cx, cy), r, facecolor='white', edgecolor=TASK_EC, linewidth=2, zorder=4)
    ax.add_patch(c)

def end_evt(ax, cx, cy, r=0.20):
    c = plt.Circle((cx, cy), r, facecolor=TASK_EC, edgecolor=TASK_EC, linewidth=2, zorder=4)
    ax.add_patch(c)
    c2 = plt.Circle((cx, cy), r*0.5, facecolor='white', edgecolor='white', zorder=5)
    ax.add_patch(c2)

def arrow(ax, x1, y1, x2, y2, color='#333333', lw=1.5):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw, mutation_scale=12),
                zorder=6)

def polyline(ax, pts, color='#333333', lw=1.5):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    ax.plot(xs, ys, color=color, lw=lw, zorder=3, solid_capstyle='round')

def note(ax, x, y, txt, ha='left', color=TEXT_GREY, fs=7.5, italic=True):
    ax.text(x, y, txt, ha=ha, va='center', fontsize=fs,
            color=color, style='italic' if italic else 'normal', linespacing=1.3)


# ─────────────────────────────────────────────────────────────────────────────
# DOMESTIC BPMN  –  no aspect='equal' so annotations have breathing room
# ─────────────────────────────────────────────────────────────────────────────
def domestic():
    fig, ax = plt.subplots(figsize=(14, 5.5))
    ax.set_xlim(-0.5, 22.5)
    ax.set_ylim(-2.2, 6.5)
    ax.axis('off')

    ax.text(11.0, 6.1, 'Domestic Declaration Process – Simplified BPMN',
            ha='center', va='center', fontsize=12, color=TEXT_DARK, fontweight='bold')

    Y        = 3.0
    Y_BYPASS = 4.8
    Y_BO     = 1.2
    Y_REJ    = -0.8

    x_start  = 0.4
    x_submit = 2.5
    x_gw1    = 5.0
    x_admin  = 7.1
    x_gw2    = 9.3
    x_bo     = 11.2
    x_gw3    = 13.4
    x_sup    = 15.8
    x_pay1   = 17.8
    x_pay2   = 19.8
    x_end    = 21.4

    # Start → Submit
    start_evt(ax, x_start, Y)
    arrow(ax, x_start + 0.20, Y, x_submit - 1.40, Y)
    task_box(ax, x_submit, Y, 'Declaration\nSubmitted', w=2.7)
    arrow(ax, x_submit + 1.35, Y, x_gw1 - 0.42, Y)
    gateway(ax, x_gw1, Y)

    # Admin bypass (upper)
    polyline(ax, [(x_gw1, Y + 0.28), (x_gw1, Y_BYPASS), (x_gw3, Y_BYPASS)])
    arrow(ax, x_gw3, Y_BYPASS, x_gw3, Y + 0.28)
    note(ax, x_gw1 + 0.5, Y_BYPASS + 0.38,
         'No administration step  (22.7% of cases)', fs=8)

    # Admin path (middle)
    arrow(ax, x_gw1 + 0.42, Y, x_admin - 1.35, Y)
    task_box(ax, x_admin, Y, 'Administration\nApproved', w=2.5)
    arrow(ax, x_admin + 1.25, Y, x_gw2 - 0.42, Y)
    gateway(ax, x_gw2, Y)

    # Budget Owner path (lower)
    polyline(ax, [(x_gw2, Y - 0.28), (x_gw2, Y_BO), (x_gw3, Y_BO)])
    arrow(ax, x_gw3, Y_BO, x_gw3, Y - 0.28)
    task_box(ax, x_bo, Y_BO, 'Budget Owner\nApproved', w=2.5, fc='#E8F4E8')
    # note well below the box
    note(ax, x_bo, Y_BO - 0.62,
         'Budget Owner inserted in 26.4% of cases', ha='center', fs=7.5)

    # Direct GW2 → GW3 (no Budget Owner)
    arrow(ax, x_gw2 + 0.42, Y, x_gw3 - 0.42, Y)
    gateway(ax, x_gw3, Y, label='+')

    # Supervisor → Payment → End
    arrow(ax, x_gw3 + 0.42, Y, x_sup - 1.60, Y)
    task_box(ax, x_sup, Y, 'Supervisor\nFinal Approved', w=2.9)
    arrow(ax, x_sup + 1.45, Y, x_pay1 - 0.85, Y)
    task_box(ax, x_pay1, Y, 'Request\nPayment', w=1.65)
    arrow(ax, x_pay1 + 0.83, Y, x_pay2 - 0.83, Y)
    task_box(ax, x_pay2, Y, 'Payment\nHandled', w=1.65, fc='#E8F4E8')
    arrow(ax, x_pay2 + 0.83, Y, x_end - 0.20, Y)
    end_evt(ax, x_end, Y)

    # Rejection loop (red, below main flow)
    polyline(ax, [(x_sup - 0.3, Y - 0.28), (x_sup - 0.3, Y_REJ),
                  (x_submit - 0.1, Y_REJ)], color=REJ_COLOR)
    arrow(ax, x_submit - 0.1, Y_REJ, x_submit - 0.1, Y - 0.28, color=REJ_COLOR)
    note(ax, (x_submit + x_sup) / 2, Y_REJ - 0.45,
         'Rejection loop (9.7% rework): Rejected by Supervisor / Administration / Employee  →  resubmission',
         ha='center', color=REJ_COLOR, fs=7.5)

    # Variant legend
    ax.text(11.0, -1.85,
            'Variant coverage:  44.0% Admin+Supervisor  |  23.6% Admin+Budget Owner+Supervisor  '
            '|  13.3% Supervisor direct  |  5.5% Pre-Approver+Supervisor  |  13.7% other/rework',
            ha='center', va='center', fontsize=7, color=TEXT_GREY, style='italic')

    plt.tight_layout(pad=0.2)
    out = os.path.join(OUT, 'domestic_bpmn.png')
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'Saved {out}')


# ─────────────────────────────────────────────────────────────────────────────
# INTERNATIONAL BPMN  –  three horizontal swimlane bands, no aspect='equal'
# ─────────────────────────────────────────────────────────────────────────────
def international():
    fig, ax = plt.subplots(figsize=(18, 9.5))
    ax.set_xlim(-1.5, 17.5)
    ax.set_ylim(-0.8, 9.8)
    ax.axis('off')

    ax.text(8.0, 9.5,
            'International Declaration Process – Simplified BPMN (Swimlane Layout)',
            ha='center', va='center', fontsize=13, color=TEXT_DARK, fontweight='bold')

    # ── Swimlane band definitions ─────────────────────────────────────────────
    # (label, y_bottom, y_top, y_center)
    lanes = [
        ('Phase 1\nPermit\nApproval',    6.4, 8.9, 7.65),
        ('Phase 2\nTravel',              3.5, 6.4, 4.95),
        ('Phase 3\nDeclaration\n& Payment', 0.3, 3.5, 1.90),
    ]
    for lbl, yb, yt, yc in lanes:
        rect = mpatches.FancyBboxPatch((-1.0, yb), 18.3, yt - yb,
                                        boxstyle='round,pad=0.0',
                                        facecolor=LANE_FC, edgecolor=LANE_EC,
                                        linewidth=1.2, zorder=1)
        ax.add_patch(rect)
        lrect = mpatches.FancyBboxPatch((-1.0, yb + 0.05), 1.0, yt - yb - 0.1,
                                         boxstyle='round,pad=0.0',
                                         facecolor='#D0DCF0', edgecolor=LANE_EC,
                                         linewidth=0.8, zorder=2)
        ax.add_patch(lrect)
        ax.text(-0.50, yc, lbl, ha='center', va='center', fontsize=8.5,
                color='#1F3864', fontweight='bold', linespacing=1.35, zorder=3)

    # ── Phase 1: Permit Approval  (y ≈ 7.65) ─────────────────────────────────
    Y1 = 7.65
    xs = 0.5
    start_evt(ax, xs, Y1)
    arrow(ax, xs + 0.20, Y1, xs + 0.90, Y1)
    task_box(ax, xs + 1.75, Y1, 'Permit\nSubmitted', w=2.4, fontsize=9)
    arrow(ax, xs + 2.95, Y1, xs + 3.75, Y1)
    task_box(ax, xs + 5.25, Y1, 'Permit Approved\n(Admin / Budget Owner)', w=3.8, fontsize=9, fc='#E8F0FB')
    arrow(ax, xs + 7.15, Y1, xs + 8.05, Y1)
    task_box(ax, xs + 9.65, Y1, 'Permit FINAL_APPROVED\nby Supervisor / Director', w=3.8, fontsize=9, fc='#E8F0FB')

    note(ax, xs + 5.25, Y1 + 0.60,
         '6.9% of cases: NO permit on record (policy violation)',
         ha='center', color=REJ_COLOR, fs=8)
    note(ax, xs + 5.25, Y1 - 0.62,
         'Permit rejection loop  →  resubmission',
         ha='center', color=REJ_COLOR, fs=8)

    # Phase 1 → Phase 2: route along TOP of Phase 2 band then drop into Start Trip
    # y=5.9 is above all Phase 2 box tops (max 5.225) but inside the Phase 2 lane (top 6.4)
    x_p1_end = xs + 11.55  # = 12.05, right edge of last Phase 1 task
    Y_TOP2 = 5.9
    polyline(ax, [(x_p1_end, Y1 - 0.28), (x_p1_end, Y_TOP2)])  # descend on right
    polyline(ax, [(x_p1_end, Y_TOP2), (2.0, Y_TOP2)])           # horizontal left above boxes
    arrow(ax, 2.0, Y_TOP2, 2.0, 4.95 + 0.28)                    # drop into Start Trip

    # ── Phase 2: Travel  (y ≈ 4.95) ──────────────────────────────────────────
    Y2 = 4.95

    task_box(ax, 2.0, Y2, 'Start Trip', w=2.2, fontsize=9, fc='#FFF4E5')
    arrow(ax, 3.10, Y2, 3.90, Y2)

    dur = mpatches.FancyBboxPatch((3.90, Y2 - 0.33), 3.4, 0.66,
                                   boxstyle='round,pad=0.05',
                                   facecolor='#FFFDE7', edgecolor='#FFC107',
                                   linewidth=1.4, linestyle='dashed', zorder=4)
    ax.add_patch(dur)
    ax.text(5.60, Y2, '~4.0 days median\n(travel duration)',
            ha='center', va='center', fontsize=8, color='#7B6000', style='italic', zorder=5)

    arrow(ax, 7.30, Y2, 8.10, Y2)
    task_box(ax, 9.20, Y2, 'End Trip', w=2.2, fontsize=9, fc='#FFF4E5')

    note(ax, 5.60, Y2 + 0.62,
         'Send Reminder: 406 cases, median 43-day delay',
         ha='center', color='#E67E22', fs=8)
    note(ax, 5.60, Y2 - 0.65,
         '707 cases: trip BEFORE permit submission  |  592 cases: no declaration filed after return',
         ha='center', color=REJ_COLOR, fs=8)

    # Phase 2 → Phase 3: route along TOP of Phase 3 band then drop into Declaration Submitted
    # y=3.0 is above all Phase 3 box tops (max 2.175) but inside the Phase 3 lane (top 3.5)
    x_p2_end = 10.30  # right edge of End Trip (x=9.20, w=2.2 → 9.20+1.10)
    Y_TOP3 = 3.0
    polyline(ax, [(x_p2_end, Y2 - 0.28), (x_p2_end, Y_TOP3)])  # descend on right
    polyline(ax, [(x_p2_end, Y_TOP3), (1.10, Y_TOP3)])           # horizontal left above boxes
    arrow(ax, 1.10, Y_TOP3, 1.10, 1.90 + 0.28)                   # drop into Declaration Submitted

    # ── Phase 3: Declaration & Payment  (y ≈ 1.90) ───────────────────────────
    Y3 = 1.90

    task_box(ax, 1.10, Y3, 'Declaration\nSubmitted', w=2.0, fontsize=9)
    arrow(ax, 2.10, Y3, 2.90, Y3)
    task_box(ax, 4.30, Y3, 'Declaration Approved\n(Admin / Budget Owner)', w=3.6, fontsize=9, fc='#D5E8F0')
    arrow(ax, 6.10, Y3, 6.90, Y3)
    task_box(ax, 8.30, Y3, 'Declaration\nFINAL_APPROVED', w=2.8, fontsize=9, fc='#D5E8F0')
    arrow(ax, 9.70, Y3, 10.50, Y3)
    task_box(ax, 11.60, Y3, 'Request\nPayment', w=2.0, fontsize=9)
    arrow(ax, 12.60, Y3, 13.40, Y3)
    task_box(ax, 14.55, Y3, 'Payment\nHandled', w=2.0, fontsize=9, fc='#E8F4E8')
    arrow(ax, 15.55, Y3, 16.15, Y3)
    end_evt(ax, 16.35, Y3)

    note(ax, 6.80, Y3 + 0.62,
         'Post-trip filing lag: 5.65 d median  |  Payment batch delay: 3.22 d median',
         ha='center', color=TEXT_GREY, fs=8)
    note(ax, 6.80, Y3 - 0.65,
         'Declaration rejection loop (24.65% rework)  →  resubmission',
         ha='center', color=REJ_COLOR, fs=8)

    # ── Legend ────────────────────────────────────────────────────────────────
    ax.text(8.0, -0.55,
            'Happy path (21.2%): Permit Submitted → Permit Approved → Start Trip → '
            'End Trip → Declaration Submitted → Declaration Approved → Request Payment → Payment Handled',
            ha='center', va='center', fontsize=7.5, color=TEXT_GREY, style='italic')

    plt.tight_layout(pad=0.2)
    out = os.path.join(OUT, 'international_bpmn.png')
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'Saved {out}')


if __name__ == '__main__':
    domestic()
    international()
    print('Done.')
