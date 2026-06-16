import logging
from datetime import datetime
from tkinter import messagebox, StringVar
from customtkinter import CTkToplevel, CTkFrame, CTkRadioButton


def setup_backup_restore_page(frames, StyleManager, csv_repository, show_frame, app):
    frame = frames["backup_restore"]
    frame.grid_columnconfigure(0, weight=1)

    header_frame = StyleManager.create_frame(frame)
    header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 40))
    header_frame.grid_columnconfigure(0, weight=1)

    StyleManager.create_label(
        header_frame,
        text="النسخ الاحتياطي واستعادة البيانات",
        font_style="heading"
    ).grid(row=0, column=0, pady=(20, 10))

    StyleManager.create_label(
        header_frame,
        text="إدارة النسخ الاحتياطية واستعادة البيانات",
        font_style="body",
        text_color=StyleManager.COLORS["text_secondary"]
    ).grid(row=1, column=0, pady=(0, 20))

    content_frame = StyleManager.create_frame(frame)
    content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
    content_frame.grid_columnconfigure(0, weight=1)

    backup_section = StyleManager.create_frame(content_frame)
    backup_section.grid(row=0, column=0, sticky="ew", pady=(0, 20))
    backup_section.grid_columnconfigure(1, weight=1)

    StyleManager.create_label(
        backup_section,
        text="💾",
        font=("Arial", 36)
    ).grid(row=0, column=0, padx=(20, 10), pady=20)

    backup_title_frame = CTkFrame(backup_section, fg_color="transparent")
    backup_title_frame.grid(row=0, column=1, sticky="nsew", pady=20)

    StyleManager.create_label(
        backup_title_frame,
        text="إنشاء نسخة احتياطية",
        font_style="subheading"
    ).grid(row=0, column=0, sticky="w")

    StyleManager.create_label(
        backup_title_frame,
        text="حفظ نسخة من البيانات الحالية",
        font_style="body",
        text_color=StyleManager.COLORS["text_secondary"]
    ).grid(row=1, column=0, sticky="w")

    def create_backup():
        try:
            backup_file = csv_repository.create_backup()
            if backup_file:
                messagebox.showinfo("نجاح", f"تم إنشاء نسخة احتياطية في: {backup_file}")
            else:
                messagebox.showerror("خطأ", "فشل إنشاء النسخة الاحتياطية.")
        except Exception as e:
            logging.error(f"Error creating backup: {str(e)}")
            messagebox.showerror("خطأ", "حدث خطأ أثناء إنشاء النسخة الاحتياطية.")

    StyleManager.create_button(
        backup_section,
        text="إنشاء نسخة احتياطية",
        width=200,
        command=create_backup
    ).grid(row=0, column=2, padx=20)

    restore_section = StyleManager.create_frame(content_frame)
    restore_section.grid(row=1, column=0, sticky="ew")
    restore_section.grid_columnconfigure(1, weight=1)

    StyleManager.create_label(
        restore_section,
        text="🔄",
        font=("Arial", 36)
    ).grid(row=0, column=0, padx=(20, 10), pady=20)

    restore_title_frame = CTkFrame(restore_section, fg_color="transparent")
    restore_title_frame.grid(row=0, column=1, sticky="nsew", pady=20)

    StyleManager.create_label(
        restore_title_frame,
        text="استعادة نسخة احتياطية",
        font_style="subheading"
    ).grid(row=0, column=0, sticky="w")

    StyleManager.create_label(
        restore_title_frame,
        text="استعادة البيانات من نسخة احتياطية سابقة",
        font_style="body",
        text_color=StyleManager.COLORS["text_secondary"]
    ).grid(row=1, column=0, sticky="w")

    def restore_backup():
        try:
            backup_files = csv_repository.get_backup_files()
            if not backup_files:
                messagebox.showerror("خطأ", "لا توجد نسخ احتياطية متاحة.")
                return

            restore_window = CTkToplevel(app)
            restore_window.geometry("600x400")
            restore_window.title("استعادة نسخة احتياطية")
            restore_window.transient(app)
            restore_window.grab_set()

            StyleManager.create_label(
                restore_window,
                text="اختر النسخة الاحتياطية للاستعادة",
                font_style="heading"
            ).pack(pady=(20, 10))

            StyleManager.create_label(
                restore_window,
                text="سيتم استبدال البيانات الحالية بالنسخة المحددة",
                font_style="body",
                text_color=StyleManager.COLORS["text_secondary"]
            ).pack(pady=(0, 20))

            backup_frame = StyleManager.create_frame(restore_window)
            backup_frame.pack(fill="both", expand=True, padx=20, pady=20)

            backup_list = CTkFrame(backup_frame, fg_color="transparent")
            backup_list.pack(fill="both", expand=True)

            selected_backup = StringVar()

            for backup in sorted(backup_files, reverse=True):
                backup_date = backup.replace("backup_", "").replace(".csv", "")
                try:
                    formatted_date = datetime.strptime(backup_date, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    formatted_date = backup_date

                radio = CTkRadioButton(
                    backup_list,
                    text=f"نسخة {formatted_date}",
                    variable=selected_backup,
                    value=backup,
                    font=StyleManager.FONTS["body"]
                )
                radio.pack(pady=5, padx=10, anchor="w")

            if backup_files:
                selected_backup.set(backup_files[0])

            buttons_frame = StyleManager.create_frame(restore_window)
            buttons_frame.pack(fill="x", padx=20, pady=20)
            buttons_frame.grid_columnconfigure(0, weight=1)
            buttons_frame.grid_columnconfigure(1, weight=1)

            def confirm_restore():
                try:
                    selected = selected_backup.get()
                    if not selected:
                        messagebox.showerror("خطأ", "يرجى اختيار نسخة احتياطية.")
                        return

                    if messagebox.askyesno("تأكيد", "هل أنت متأكد من استعادة هذه النسخة؟ سيتم استبدال البيانات الحالية."):
                        if csv_repository.restore_backup(selected):
                            messagebox.showinfo("نجاح", "تم استعادة النسخة الاحتياطية بنجاح.")
                            restore_window.destroy()
                        else:
                            messagebox.showerror("خطأ", "فشل استعادة النسخة الاحتياطية.")
                except Exception as e:
                    logging.error(f"Error restoring backup: {str(e)}")
                    messagebox.showerror("خطأ", "حدث خطأ أثناء استعادة النسخة الاحتياطية.")

            StyleManager.create_button(
                buttons_frame,
                text="استعادة",
                width=200,
                command=confirm_restore
            ).grid(row=0, column=0, padx=10)

            StyleManager.create_button(
                buttons_frame,
                text="إلغاء",
                style="secondary",
                width=200,
                command=restore_window.destroy
            ).grid(row=0, column=1, padx=10)

        except Exception as e:
            logging.error(f"Error in restore backup window: {str(e)}")
            messagebox.showerror("خطأ", "حدث خطأ أثناء فتح نافذة الاستعادة.")

    StyleManager.create_button(
        restore_section,
        text="استعادة نسخة احتياطية",
        width=200,
        command=restore_backup
    ).grid(row=0, column=2, padx=20)

    back_frame = StyleManager.create_frame(frame)
    back_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
    back_frame.grid_columnconfigure(0, weight=1)

    StyleManager.create_button(
        back_frame,
        text="العودة",
        style="secondary",
        width=200,
        command=lambda: show_frame(frames["home"])
    ).grid(row=0, column=0)
