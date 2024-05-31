import asyncio
from data_fetcher import fetch_all_consumption

if __name__ == '__main__':
    
    uri = 'http://localhost:8766/graphql'
    protocols_url = 'http://127.0.0.1:8000'
    interval = 10
    delay = 5
    sftp_host = '192.168.56.101'
    sftp_port = 22
    sftp_username = 'hpccdemo'
    sftp_password = 'hpccdemo'
    remote_path = '/var/lib/HPCCSystems/mydropzone'
    limit = 24
    offset = 0
    start_date = '2007-01-01'

    try:
        asyncio.run(fetch_all_consumption(uri, protocols_url, sftp_host, sftp_port, sftp_username, sftp_password, remote_path, interval, limit, offset, delay, start_date))
    except KeyboardInterrupt:
        print("\nColeta de dados encerrando via interrupção pelo usuário...")
    except Exception as e:
        print(f"\nErro durante a execução da coleta de dados: {str(e)}")
    finally:
        print("Coleta de dados encerrada com sucesso.")
