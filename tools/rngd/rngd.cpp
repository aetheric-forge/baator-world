// tools/rngd/rngd.cpp
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <atomic>
#include <chrono>
#include <cstring>
#include <iostream>
#include <mutex>
#include <random>
#include <string>
#include <thread>
#include <vector>

static constexpr int PORT = 4444;
static std::random_device rd;
static thread_local std::mt19937_64 rng(rd()); // thread-local PRNG
static std::atomic<bool> running{true};

static void send_line(int fd, const std::string& s) {
    ::send(fd, s.c_str(), s.size(), 0);
}

static void handle_client(int fd) {
    std::string buf;
    buf.reserve(256);
    char tmp[128];

    while (running) {
        ssize_t n = recv(fd, tmp, sizeof(tmp), 0);
        if (n <= 0) break;
        buf.append(tmp, tmp + n);

        size_t pos;
        while ((pos = buf.find('\n')) != std::string::npos) {
            std::string line = buf.substr(0, pos);
            buf.erase(0, pos + 1);

            // trim CR
            if (!line.empty() && line.back() == '\r') line.pop_back();

            if (line == "PING") { send_line(fd, "OK PONG\n"); continue; }
            if (line == "VER")  { send_line(fd, "OK RNG/1\n"); continue; }

            // RAND low high
            if (line.rfind("RAND ", 0) == 0) {
                long long low, high;
                if (sscanf(line.c_str(), "RAND %lld %lld", &low, &high) == 2 && low <= high) {
                    std::uniform_int_distribution<long long> dist(low, high);
                    auto v = dist(rng);
                    send_line(fd, "OK " + std::to_string(v) + "\n");
                } else {
                    send_line(fd, "ERR usage: RAND <low> <high>\n");
                }
                continue;
            }

            // DICE dN
            if (line.rfind("DICE d", 0) == 0) {
                long long sides;
                if (sscanf(line.c_str(), "DICE d%lld", &sides) == 1 && sides >= 1) {
                    std::uniform_int_distribution<long long> dist(1, sides);
                    auto v = dist(rng);
                    send_line(fd, "OK " + std::to_string(v) + "\n");
                } else {
                    send_line(fd, "ERR usage: DICE d<sides>\n");
                }
                continue;
            }

            send_line(fd, "ERR unknown\n");
        }
    }
    close(fd);
}

int main() {
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) { perror("socket"); return 1; }

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons(PORT);
    if (bind(server_fd, (sockaddr*)&addr, sizeof(addr)) < 0) { perror("bind"); return 1; }
    if (listen(server_fd, 64) < 0) { perror("listen"); return 1; }

    std::cerr << "rngd listening on :" << PORT << "\n";

    while (running) {
        sockaddr_in caddr{};
        socklen_t clen = sizeof(caddr);
        int cfd = accept(server_fd, (sockaddr*)&caddr, &clen);
        if (cfd < 0) { perror("accept"); continue; }
        std::thread(handle_client, cfd).detach();
    }
    close(server_fd);
    return 0;
}
