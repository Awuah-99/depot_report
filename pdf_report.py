#!/usr/bin/env python3
"""
pdf_report.py: Generates PDF reports using Matplotlib.
"""
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from app_logger import setup_logger

logger = setup_logger(__name__)

STATUS_ORDER = [
    'ordered', 'approved', 'good_standing', 'brv_checked', 
    'depot_manager', 'loaded', 'order_released', 'marked',
    'bdc_decline', 'depot_manager_decline', 'bdc_cancel_order', 'ppmc_cancel_order'
]

STATUS_DISPLAY_NAMES = {
    'ordered': 'Ordered', 'approved': 'Approved', 'good_standing': 'Good Standing',
    'brv_checked': 'BRV Checked', 'depot_manager': 'Depot Manager', 'loaded': 'Loaded',
    'order_released': 'Order Released', 'marked': 'Marked', 'bdc_decline': 'BDC Decline',
    'depot_manager_decline': 'Depot Manager Decline', 'bdc_cancel_order': 'BDC Cancel Order',
    'ppmc_cancel_order': 'PPMC Cancel Order',
}

DISPLAY_COLUMNS = [
    'order_number', 'product', 'volume', 'brv_number', 
    'ex_ref_price', 'order_date', 'bdc', 'depot'
]

PRODUCT_COLORS = {
    'PMS': '#2ecc71',
    'AGO': '#3498db',
    'Other': '#95a5a6',
}

ROWS_PER_PAGE = 22

def classify_product(product: str) -> str:
    value = str(product).upper().strip()
    if not value or value in ('NAN', 'NONE', ''):
        return 'Other'
    if 'PMS' in value or 'PREMIUM MOTOR SPIRIT' in value or 'PETROL' in value:
        return 'PMS'
    if 'AGO' in value or 'AUTOMOTIVE GAS OIL' in value or 'DIESEL' in value:
        return 'AGO'
    return 'Other'

def default_pdf_path(depot_name: str = "depot") -> str:
    reports_dir = Path('reports')
    reports_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return str(reports_dir / f'{depot_name}_report_{timestamp}.pdf')


class PDFReportGenerator:
    def generate(self, df: pd.DataFrame, output_path: str) -> bool:
        if df is None or df.empty:
            logger.warning("No data available for PDF report")
            return False

        if 'product' not in df.columns and 'products' in df.columns:
            df = df.rename(columns={'products': 'product'})

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        try:
            with PdfPages(str(output)) as pdf:
                self._write_summary_page(pdf, df)
                
                unique_statuses = df['status'].unique()
                sorted_statuses = sorted(
                    unique_statuses,
                    key=lambda x: (STATUS_ORDER.index(x) if x in STATUS_ORDER else 99, x)
                )
                
                for status in sorted_statuses:
                    status_df = df[df['status'] == status]
                    if not status_df.empty:
                        self._write_table_pages(pdf, status, status_df)
                        
            logger.info(f"PDF report saved to {output}")
            return True
        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            return False

    def _write_summary_page(self, pdf: PdfPages, df: pd.DataFrame) -> None:
        product_counts = {'PMS': 0, 'AGO': 0, 'Other': 0}
        if 'product' in df.columns:
            for product in df['product']:
                category = classify_product(product)
                product_counts[category] += 1
                
        total_orders = len(df)
        generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        fig = plt.figure(figsize=(11, 8.5))
        fig.suptitle('DAILY ORDER REPORT', fontsize=16, fontweight='bold', y=0.97)
        fig.text(0.5, 0.92, f'Generated: {generated_at}', ha='center', fontsize=10)

        # Pie Chart
        ax_chart = fig.add_axes([0.1, 0.35, 0.45, 0.5])
        labels, sizes, colors = self._pie_chart_data(product_counts)
        
        if sizes:
            wedges, texts, autotexts = ax_chart.pie(
                sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                startangle=90, textprops={'fontsize': 10}
            )
            for autotext in autotexts:
                autotext.set_fontsize(9)
            ax_chart.set_title('Total Orders by Product', fontsize=12, pad=10)
        else:
            ax_chart.text(0.5, 0.5, 'No product data', ha='center', va='center')
            ax_chart.axis('off')

        # Summary Text
        ax_summary = fig.add_axes([0.58, 0.2, 0.38, 0.65])
        ax_summary.axis('off')
        
        summary_lines = [
            f'Total orders: {total_orders}',
            '',
            'Product breakdown:',
            f"  PMS:   {product_counts['PMS']}",
            f"  AGO:   {product_counts['AGO']}",
            f"  Other: {product_counts['Other']}",
            '',
            'Status Breakdown:',
        ]
        
        # Add status counts in logical order
        status_counts = df['status'].value_counts()
        for status in STATUS_ORDER:
            if status in status_counts.index:
                display_name = STATUS_DISPLAY_NAMES.get(status, status.replace('_', ' ').title())
                summary_lines.append(f'  {display_name}: {status_counts[status]}')

        ax_summary.text(0, 1, '\n'.join(summary_lines), va='top', fontsize=10, family='monospace')

        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

    def _pie_chart_data(self, product_counts: dict) -> tuple:
        """Build pie chart labels, sizes, and colors (excluding zero counts)."""
        labels, sizes, colors = [], [], []
        for category in ('PMS', 'AGO', 'Other'):
            count = product_counts.get(category, 0)
            if count > 0:
                labels.append(f'{category}\n({count})')
                sizes.append(count)
                colors.append(PRODUCT_COLORS[category])
        return labels, sizes, colors

    def _write_table_pages(self, pdf: PdfPages, status: str, df: pd.DataFrame) -> None:
        """Write one or more pages for a status section."""
        display_name = STATUS_DISPLAY_NAMES.get(status, status.replace('_', ' ').title())
        
        # Select only display columns that exist
        cols_to_show = [c for c in DISPLAY_COLUMNS if c in df.columns]
        display_df = df[cols_to_show].copy()
        
        # Format numeric and date columns for readability
        if 'volume' in display_df.columns:
            display_df['volume'] = pd.to_numeric(display_df['volume'], errors='coerce').apply(
                lambda x: f"{x:,.2f}" if pd.notna(x) else ""
            )
        if 'ex_ref_price' in display_df.columns:
            display_df['ex_ref_price'] = pd.to_numeric(display_df['ex_ref_price'], errors='coerce').apply(
                lambda x: f"{x:.2f}" if pd.notna(x) else ""
            )
        if 'order_date' in display_df.columns:
            display_df['order_date'] = pd.to_datetime(display_df['order_date'], errors='coerce').apply(
                lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ""
            )
            
        # Fill NaNs with empty string for table rendering
        display_df = display_df.fillna('').astype(str)

        total_rows = len(display_df)
        total_pages = (total_rows - 1) // ROWS_PER_PAGE + 1 if total_rows > 0 else 1

        for start in range(0, total_rows, ROWS_PER_PAGE):
            chunk = display_df.iloc[start:start + ROWS_PER_PAGE]
            page_num = start // ROWS_PER_PAGE + 1

            fig, ax = plt.subplots(figsize=(11, 8.5))
            ax.axis('off')

            title = f'{display_name} ({total_rows} orders)'
            if total_pages > 1:
                title += f' — page {page_num}/{total_pages}'
            ax.set_title(title, fontsize=13, fontweight='bold', pad=20)

            col_labels = [col.replace('_', ' ').title() for col in cols_to_show]
            
            table = ax.table(
                cellText=chunk.values,
                colLabels=col_labels,
                loc='center',
                cellLoc='left',
            )
            
            table.auto_set_font_size(False)
            table.set_fontsize(7)
            table.scale(1, 1.4)

            # Styling (Matches your existing design)
            for (row, col), cell in table.get_celld().items():
                if row == 0:
                    cell.set_facecolor('#2c3e50')
                    cell.set_text_props(color='white', fontweight='bold')
                elif row % 2 == 0:
                    cell.set_facecolor('#f8f9fa')
                    
            # Add footer with total count on the last page (Matches your PDF sample)
            if page_num == total_pages:
                fig.text(0.5, 0.02, f'Total# for {display_name} is {total_rows}', 
                         ha='center', fontsize=10, style='italic')

            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
