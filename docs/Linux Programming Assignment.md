```
Linux Programming Assignment
```
```
Nhóm thực tập Nhúng – dự án gNodeB 5G VHT
```
```
Hòa Lạc – 7/7/
```
1. Viết chương trình C trên Linux chạy 3 thread SAMPLE, LOGGING, INPUT. Trong đó:
- Thread SAMPLE thực hiện vô hạn lần nhiệm vụ sau với chu kì X ns. Nhiệm vụ là đọc thời
    gian hệ thống hiện tại (chính xác đến đơn vị ns) vào biến T.
- Thread INPUT kiểm tra file “freq.txt” để xác định chu kỳ X (của thread SAMPLE) có bị
    thay đổi không?, nếu có thay đổi thì cập nhật lại chu kỳ X. Người dùng có thể echo giá trị chu kỳ X mong muốn vào file “freq.txt” để thread INPUT cập nhật lại X.
- Thread LOGGING chờ khi biến T được cập nhật mới, thì ghi giá trị biến T và giá trị
    interval (offset giữa biến T hiện tại và biến T của lần ghi trước) ra file có tên
    “time_and_interval.txt”.
2. Viết shell script để thay đổi lại giá trị chu kỳ X trong file “freq.txt” sau mỗi 1 phút. Các giá trị X lần lượt được ghi như sau: 1000000 ns, 100000 ns, 10000 ns, 1000 ns, 100ns.
3. Chạy shell script + chương trình C trong vòng 5 phút, sau đó dừng chương trình C.
4. Thực hiện khảo sát file “time_and_interval.txt”: Vẽ đồ thị giá trị interval đối với mỗi giá trị chu kỳ X và đánh giá.

Note: Có thể sử dụng cuốn The Linux Programming Interface, by Michael Kerrisk (2010) để tra
cứu. Ví dụ với multithreading có thể tham khảo Chương 29: Thread: Introduction để xem cách tạo thread. Với đo đạc thời gian có thể tham khảo Chương 23: Timers and Sleeping.


