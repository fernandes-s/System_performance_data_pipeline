import streamlit as st


def section_header(title: str, caption: str | None = None) -> None:
    """
    Render a standard section header with an optional caption.

    Args:
        title (str): Section title.
        caption (str | None): Optional supporting caption.
    """
    st.subheader(title)
    if caption:
        st.caption(caption)


def show_empty_state(
    message: str = "No data available.",
    suggestion: str | None = None,
) -> None:
    """
    Render a standard empty-state message.

    Args:
        message (str): Main empty-state message.
        suggestion (str | None): Optional follow-up suggestion.
    """
    st.info(message)
    if suggestion:
        st.caption(suggestion)


def show_status_badge(status: str) -> None:
    """
    Render a simple text-based status badge using Streamlit feedback components.

    Args:
        status (str): Status label.
    """
    normalized = str(status).strip().lower()

    if normalized in {"healthy", "ok", "normal"}:
        st.success(f"Status: {status}")
    elif normalized in {"warning", "caution"}:
        st.warning(f"Status: {status}")
    elif normalized in {"critical", "error", "failed"}:
        st.error(f"Status: {status}")
    else:
        st.info(f"Status: {status}")


def show_kpi_card(
    label: str,
    value,
    delta=None,
    help_text: str | None = None,
) -> None:
    """
    Render a KPI using Streamlit's metric component.

    Args:
        label (str): KPI label.
        value: KPI value to display.
        delta: Optional delta value.
        help_text (str | None): Optional tooltip/help text.
    """
    st.metric(
        label=label,
        value=value,
        delta=delta,
        help=help_text,
    )


def show_dataframe_preview(
    df,
    title: str | None = None,
    max_rows: int = 10,
    use_container_width: bool = True,
) -> None:
    """
    Render a compact dataframe preview.

    Args:
        df: DataFrame to display.
        title (str | None): Optional preview title.
        max_rows (int): Maximum number of rows to display.
        use_container_width (bool): Whether to stretch to container width.
    """
    if title:
        st.markdown(f"**{title}**")

    if df is None or df.empty:
        show_empty_state("No rows to display.")
        return

    st.dataframe(
        df.head(max_rows),
        use_container_width=use_container_width,
        hide_index=True,
    )


def show_chart_or_empty(fig, empty_message: str = "No chart data available.") -> None:
    """
    Display a Plotly chart if it contains data, otherwise show an empty-state message.

    Args:
        fig: Plotly figure.
        empty_message (str): Fallback message if the figure is empty.
    """
    if fig is None or not getattr(fig, "data", None):
        show_empty_state(empty_message)
        return

    st.plotly_chart(fig, use_container_width=True)


def two_column_kpis(kpis: list[dict]) -> None:
    """
    Render KPI cards in a two-column layout.

    Args:
        kpis (list[dict]): List of KPI definitions. Each item should contain:
            - label
            - value
            - optional delta
            - optional help_text
    """
    if not kpis:
        return

    cols = st.columns(2)

    for idx, kpi in enumerate(kpis):
        with cols[idx % 2]:
            show_kpi_card(
                label=kpi.get("label", "Metric"),
                value=kpi.get("value", "N/A"),
                delta=kpi.get("delta"),
                help_text=kpi.get("help_text"),
            )


def four_column_kpis(kpis: list[dict]) -> None:
    """
    Render KPI cards in a four-column layout.

    Args:
        kpis (list[dict]): List of KPI definitions. Each item should contain:
            - label
            - value
            - optional delta
            - optional help_text
    """
    if not kpis:
        return

    cols = st.columns(4)

    for idx, kpi in enumerate(kpis[:4]):
        with cols[idx]:
            show_kpi_card(
                label=kpi.get("label", "Metric"),
                value=kpi.get("value", "N/A"),
                delta=kpi.get("delta"),
                help_text=kpi.get("help_text"),
            )