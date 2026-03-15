from app.database import get_db_connection

class NotificationService:
    def add_notification(self, message, type='info'):
        """Create a new notification"""
        conn = get_db_connection()
        if not conn:
            return None
        
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO notifications (message, type, is_read, created_at)
                VALUES (%s, %s, FALSE, CURRENT_TIMESTAMP)
                RETURNING id
            """, (message, type))
            conn.commit()
            return cur.fetchone()[0]
        except Exception as e:
            conn.rollback()
            print(f"Error adding notification: {e}")
            return None
        finally:
            conn.close()

    def get_notifications(self, unread_only=True, limit=10):
        """Fetch notifications"""
        conn = get_db_connection()
        if not conn:
            return []

        try:
            cur = conn.cursor()
            query = """
                SELECT id, message, type, is_read, TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as time
                FROM notifications
            """
            if unread_only:
                query += " WHERE is_read = FALSE"
            
            query += " ORDER BY created_at DESC LIMIT %s"
            
            cur.execute(query, (limit,))
            cols = ['id', 'message', 'type', 'is_read', 'time']
            results = [dict(zip(cols, row)) for row in cur.fetchall()]
            return results
        except Exception as e:
            print(f"Error fetching notifications: {e}")
            return []
        finally:
            conn.close()

    def get_unread_count(self):
        """Get count of unread notifications"""
        conn = get_db_connection()
        if not conn: return 0
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM notifications WHERE is_read = FALSE")
            return int(cur.fetchone()[0])
        except Exception as e:
            print(f"Error fetching notification count: {e}")
            return 0
        finally:
            conn.close()

    def mark_as_read(self, notification_id):
        """Mark a specific notification as read"""
        conn = get_db_connection()
        if not conn: return False
        
        try:
            cur = conn.cursor()
            cur.execute("UPDATE notifications SET is_read = TRUE WHERE id = %s", (notification_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error marking notification read: {e}")
            return False
        finally:
            conn.close()

    def mark_all_read(self):
        """Mark all notifications as read"""
        conn = get_db_connection()
        if not conn: return False
        
        try:
            cur = conn.cursor()
            cur.execute("UPDATE notifications SET is_read = TRUE WHERE is_read = FALSE")
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            conn.close()