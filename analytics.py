"""Daily analytics engine — computes average bill and rating stats per restaurant."""

from datetime import date, datetime, timezone

from sqlalchemy import func

from models import DailyStat, Review, db


def compute_daily_stats(target_date: date | None = None):
    """Recompute daily stats for every restaurant that has reviews on *target_date*."""
    target_date = target_date or date.today()

    rows = (
        db.session.query(
            Review.restaurant_id,
            func.count(Review.id).label("review_count"),
            func.avg(Review.bill_amount).label("avg_bill"),
            func.avg(Review.rating).label("avg_rating"),
            func.min(Review.bill_amount).label("min_bill"),
            func.max(Review.bill_amount).label("max_bill"),
        )
        .filter(Review.visit_date == target_date)
        .group_by(Review.restaurant_id)
        .all()
    )

    for row in rows:
        stat = DailyStat.query.filter_by(
            restaurant_id=row.restaurant_id, date=target_date
        ).first()

        if stat:
            stat.review_count = row.review_count
            stat.avg_bill = row.avg_bill
            stat.avg_rating = row.avg_rating
            stat.min_bill = row.min_bill
            stat.max_bill = row.max_bill
            stat.computed_at = datetime.now(timezone.utc)
        else:
            stat = DailyStat(
                restaurant_id=row.restaurant_id,
                date=target_date,
                review_count=row.review_count,
                avg_bill=row.avg_bill,
                avg_rating=row.avg_rating,
                min_bill=row.min_bill,
                max_bill=row.max_bill,
            )
            db.session.add(stat)

    db.session.commit()
    return len(rows)
